odoo.define('ks_dashboard_ninja_pro_list.ks_dashboard_graph_preview', function (require) {
    "use strict";

    var common = require('web.form_common');
    var core = require('web.core');
     var session = require('web.session');
     var utils = require('web.utils');
    var formats = require('web.formats');
    var utils = require('web.utils');
    var config = require('web.config');
    var Model = require('web.Model');

    var QWeb = core.qweb;
    var ajax = require('web.ajax');


    var MAX_LEGEND_LENGTH = 25 * (Math.max(1, config.device.size_class));

    var KsGraphPreview = common.AbstractField.extend({





        //In odoo 10 there is no option to catch change of other field value other than this.
        start: function() {
            this.field_manager.on("view_content_has_changed", this, this.preview_update);
            this.ks_set_default_chart_view();
            core.bus.on("DOM_updated", this, function () {
                if(this.shouldRenderChart && $.find('#ksMyChart').length>0) this._renderChart();
            });
            return this._super();
        },

        preview_update : function(e){
            var self = this;
            new Model('ks_dashboard_ninja.item').call('ks_view_content_change',[],{}).then(function(result){
                if (result){
                    self.render_value();
                }
            });
        },


        init: function (parent, state, params) {
            this._super.apply(this, arguments);
            this.state = {'data':[]};
//            this.fields = this.view.get_fields_values();
                jsLibs:['/ks_dashboard_ninja/static/lib/js/Chart.bundle.min.js'];
                cssLibs:['/ks_dashboard_ninja/static/lib/css/Chart.min.css'];

        },


        ks_set_default_chart_view: function () {
         Chart.plugins.unregister(ChartDataLabels);
            Chart.plugins.register({
                afterDraw: function (chart) {
                    if (chart.data.labels.length === 0) {
                        // No data is present
                        var ctx = chart.chart.ctx;
                        var width = chart.chart.width;
                        var height = chart.chart.height
                        chart.clear();

                        ctx.save();
                        ctx.textAlign = 'center';
                        ctx.textBaseline = 'middle';
                        ctx.font = "3rem 'Lucida Grande'";
                        ctx.fillText('No data available', width / 2, height / 2);
                        ctx.restore();
                    }
                }
            });
        },

        render_value: function () {
            this.$el.empty()
            this.fields = this.view.get_fields_values();
            //To handel empty selection in item form view (v11 issue)
            if (this.fields.ks_dashboard_item_type && this.fields.ks_dashboard_item_type !== 'ks_tile' && this.fields.ks_dashboard_item_type !== 'ks_kpi' && this.fields.ks_dashboard_item_type !== 'ks_list_view'){
                if(this.fields.ks_model_id){
                    if (this.fields.ks_chart_groupby_type == 'date_type' && !this.fields.ks_chart_date_groupby) {
                        return this.$el.append($('<div>').text("Select Group by date to create chart based on date groupby"));
                    }else if(this.fields.ks_chart_data_count_type==="count" && !this.fields.ks_chart_relation_groupby){
                        this.$el.append($('<div>').text("Select Group By to create chart view"));
                    }else if(this.fields.ks_chart_data_count_type!=="count" && (this.fields.ks_chart_measure_field.length === 0 || (this.fields.ks_chart_measure_field.length>0?this.fields.ks_chart_measure_field[0][2].length===0:false)|| !this.fields.ks_chart_relation_groupby )){
                        this.$el.append($('<div>').text("Select Measure and Group By to create chart view"));
                    }else if(!this.fields.ks_chart_data_count_type){
                        this.$el.append($('<div>').text("Select Chart Data Count Type"));
                    }else{
                        this._getChartData();
                    }
                }else{
                    this.$el.append($('<div>').text("Select a Model first."));
                }
            }
        },


         _getChartData: function(){
            var field = this.fields;
            var ks_chart_name;
            var self = this;
            self.shouldRenderChart = true;
            if (field.name) ks_chart_name = field.name;
            else if (field.ks_model_name) ks_chart_name = this.field_manager.fields.ks_model_id.current_display;
            else ks_chart_name = "Name";

            this.chart_data = JSON.parse(this.fields.ks_chart_data);

            if(!this.chart_data) return ;
            this.chart_type = this.fields.ks_dashboard_item_type.split('_')[1];
//            this.chart_type = this.chart_data.ks_chart_type.split('_')[1];

            var $chartContainer = $(QWeb.render('ks_chart_form_view_container', {
                ks_chart_name: ks_chart_name
            }));
            this.$el.append($chartContainer);

            switch (this.chart_type) {
                case "pie":
                case "doughnut":
                case "polarArea":
                    this.chart_family = "circle";
                    break;
                case "bar":
                case "horizontalBar":
                case "line":
                case "area":
                    this.chart_family = "square"
                    break;
                default:
                    this.chart_family = "none";
                    break;

            }


            if(this.chart_family === "circle"){
                if (this.chart_data['labels'].length > 30){
                    this.$el.find(".card-body").empty().append($("<div style='font-size:18px;'>Too many records for selected Chart Type. Consider using <strong>Domain</strong> to filter records or <strong>Record Limit</strong> to limit the no of records under <strong>30.</strong>"));
                    return ;
                }
            }
                var self = this;
                 var chart_plugin = [];
                if (this.fields.ks_show_data_value) {
                    chart_plugin.push(ChartDataLabels);
                }

                 if (this.$el.find('#ksMyChart').length>0){
                    this._renderChart();
                }

        },

         _renderChart: function(){
            var self = this;
            if(self.fields.ks_chart_measure_field_2.length>0 && self.chart_data.ks_chart_type === 'ks_bar_chart'){
                var scales  = {}
                scales.yAxes = [
                    {
                        type: "linear",
                        display: true,
                        position: "left",
                        id: "y-axis-0",
                        gridLines:{
                            display: false
                        },
                        labels: {
                            show:true,
                        }
                    },
                    {
                        type: "linear",
                        display: true,
                        position: "right",
                        id: "y-axis-1",
                        labels: {
                            show:true,
                        },
                        ticks: {
                            beginAtZero: true,
                            callback : function(value, index, values){
                                var ks_selection = self.chart_data.ks_selection;
                                if (ks_selection === 'monetary'){
                                    var ks_currency_id = self.chart_data.ks_currency;
                                    var ks_data = self.ksNumFormatter(value,1);
                                    ks_data = self.ks_monetary(ks_data, ks_currency_id);
                                    return ks_data;
                                }
                                else if (ks_selection === 'custom'){
                                    var ks_field = self.chart_data.ks_field;
                                    return self.ksNumFormatter(value,1) +' '+ ks_field;
                                }
                                else{
                                    return self.ksNumFormatter(value,1);
                                }
                            },
                        }
                    }
                ];
            }


            var $chartContainer = self.$el.find('#ksMyChart');
            var chart_plugin = [];
            if (self.fields.ks_show_data_value) {
                chart_plugin.push(ChartDataLabels);
            }
            if ($chartContainer[0]){this.ksMyChart = new Chart($chartContainer[0], {
                type: this.chart_type === "area" ? "line" : this.chart_type,
                plugins: chart_plugin,
                data: {
                    labels: this.chart_data['labels'],
                    datasets: this.chart_data.datasets,
                },
               options: {
                    maintainAspectRatio: false,
                    animation: {
                        easing: 'easeInQuad',
                    },
                    legend: {
                            display: self.fields.ks_hide_legend,
                    },
                    layout: {
                                padding: {
                                    bottom: 0,
                                }
                            },
                    scales:scales,
                    plugins: {
                        datalabels: {
                            backgroundColor: function(context) {
                                return context.dataset.backgroundColor;
                            },
                            borderRadius: 4,
                            color: 'white',
                            font: {
                                weight: 'bold'
                            },
                            anchor: 'center',
                            display: 'auto',
                            clamp: true,
                            formatter : function(value, ctx) {
                                let sum = 0;
                                let dataArr = ctx.dataset.data;
                                dataArr.map(data => {
                                    sum += data;
                                });
                                let percentage = sum === 0 ? 0 + "%" : (value*100 / sum).toFixed(2)+"%";
                                return percentage;
                            },
                        },
                    },

                }
            })};
            if($("canvas").height() < 250) $("canvas").height(250);

        self.ksChartColors(this.fields.ks_chart_item_color, this.ksMyChart, this.chart_type, this.chart_family, this.fields.ks_bar_chart_stacked, this.fields.ks_semi_circle_chart, this.fields.ks_show_data_value);


        },

        ksNumFormatter: function (num, digits) {
            var negative;
            var si = [{
                    value: 1,
                    symbol: ""
                },
                {
                    value: 1E3,
                    symbol: "k"
                },
                {
                    value: 1E6,
                    symbol: "M"
                },
                {
                    value: 1E9,
                    symbol: "G"
                },
                {
                    value: 1E12,
                    symbol: "T"
                },
                {
                    value: 1E15,
                    symbol: "P"
                },
                {
                    value: 1E18,
                    symbol: "E"
                }
            ];
            if(num<0){
                num = Math.abs(num)
                negative = true
            }
            var rx = /\.0+$|(\.[0-9]*[1-9])0+$/;
            var i;
            for (i = si.length - 1; i > 0; i--) {
                if (num >= si[i].value) {
                    break;
                }
            }
            if(negative){
                return "-" +(num / si[i].value).toFixed(digits).replace(rx, "$1") + si[i].symbol;
            }else{
                return (num / si[i].value).toFixed(digits).replace(rx, "$1") + si[i].symbol;
            }
        },
        ks_monetary: function(value,currency_id){
            var currency = session.get_currency(currency_id);
            if (!currency) {
                return value;
            }
            if (currency.position === "after") {
                return value += ' ' + currency.symbol;
            } else {
                return currency.symbol + ' ' + value;
            }
        },

        ksChartColors: function (palette, ksMyChart, ksChartType, ksChartFamily, stack, semi_circle,ks_show_data_value) {
            var currentPalette = "cool";
            var self = this;
            if (!palette) palette = currentPalette;
            currentPalette = palette;

            /*Gradients
              The keys are percentage and the values are the color in a rgba format.
              You can have as many "color stops" (%) as you like.
              0% and 100% is not optional.*/
            var gradient;
            switch (palette) {
                case 'cool':
                    gradient = {
                        0: [255, 255, 255, 1],
                        20: [220, 237, 200, 1],
                        45: [66, 179, 213, 1],
                        65: [26, 39, 62, 1],
                        100: [0, 0, 0, 1]
                    };
                    break;
                case 'warm':
                    gradient = {
                        0: [255, 255, 255, 1],
                        20: [254, 235, 101, 1],
                        45: [228, 82, 27, 1],
                        65: [77, 52, 47, 1],
                        100: [0, 0, 0, 1]
                    };
                    break;
                case 'neon':
                    gradient = {
                        0: [255, 255, 255, 1],
                        20: [255, 236, 179, 1],
                        45: [232, 82, 133, 1],
                        65: [106, 27, 154, 1],
                        100: [0, 0, 0, 1]
                    };
                    break;

                case 'default':
                    var color_set = ['#F04F65','#53cfce', '#f69032', '#fdc233', '#36a2ec', '#8a79fd', '#b1b5be', '#1c425c', '#8c2620', '#71ecef', '#0b4295', '#f2e6ce', '#1379e7']
            }



            //Find datasets and length
            var chartType = ksMyChart.config.type;
            if (ksMyChart.config.data.datasets[0]){
                switch (chartType) {
                    case "pie":
                    case "doughnut":
                    case "polarArea":
                        var datasets = ksMyChart.config.data.datasets[0];
                        var setsCount = datasets.data.length;
                        break;
                    case "bar":
                    case "horizontalBar":
                    case "line":
                        var datasets = ksMyChart.config.data.datasets;
                        var setsCount = datasets.length;
                        break;
                }
            }
            //Calculate colors
            var chartColors = [];


            if (palette !== "default") {
                //Get a sorted array of the gradient keys
                var gradientKeys = Object.keys(gradient);
                gradientKeys.sort(function (a, b) {
                    return +a - +b;
                });
                for (var i = 0; i < setsCount; i++) {
                    var gradientIndex = (i + 1) * (100 / (setsCount + 1)); //Find where to get a color from the gradient
                    for (var j = 0; j < gradientKeys.length; j++) {
                        var gradientKey = gradientKeys[j];
                        if (gradientIndex === +gradientKey) { //Exact match with a gradient key - just get that color
                            chartColors[i] = 'rgba(' + gradient[gradientKey].toString() + ')';
                            break;
                        } else if (gradientIndex < +gradientKey) { //It's somewhere between this gradient key and the previous
                            var prevKey = gradientKeys[j - 1];
                            var gradientPartIndex = (gradientIndex - prevKey) / (gradientKey - prevKey); //Calculate where
                            var color = [];
                            for (var k = 0; k < 4; k++) { //Loop through Red, Green, Blue and Alpha and calculate the correct color and opacity
                                color[k] = gradient[prevKey][k] - ((gradient[prevKey][k] - gradient[gradientKey][k]) * gradientPartIndex);
                                if (k < 3) color[k] = Math.round(color[k]);
                            }
                            chartColors[i] = 'rgba(' + color.toString() + ')';
                            break;
                        }
                    }
                }
            } else {
                for (var i = 0, counter = 0; i < setsCount; i++, counter++) {
                    if (counter >= color_set.length) counter = 0; // reset back to the beginning

                    chartColors.push(color_set[counter]);
                }

            }

            var datasets = ksMyChart.config.data.datasets;
            var options = ksMyChart.config.options;

            options.legend.labels.usePointStyle = true;
            if (ksChartFamily == "circle") {
                if(ks_show_data_value){
                    options.legend.position = 'top';
                    options.layout.padding.top = 10;
                    options.layout.padding.bottom = 20;
                }else{
                    options.legend.position = 'bottom';
                }


                options.plugins.datalabels.align = 'center';
                options.plugins.datalabels.anchor = 'end';
                options.plugins.datalabels.borderColor = 'white';
                options.plugins.datalabels.borderRadius = 25;
                options.plugins.datalabels.borderWidth = 2;
                options.plugins.datalabels.clamp = true;
                options.plugins.datalabels.clip = false;

                options.legend.position = 'bottom';
                options.tooltips.callbacks = {
                                           title: function(tooltipItem, data) {
                                                var ks_self = self;
                                                var k_amount = data.datasets[tooltipItem[0].datasetIndex]['data'][tooltipItem[0].index];
                                                var ks_selection = ks_self.chart_data.ks_selection;
                                                if (ks_selection === 'monetary'){
                                                    var ks_currency_id = ks_self.chart_data.ks_currency;
                                                    k_amount = self.ks_monetary(k_amount, ks_currency_id);
                                                    return data.datasets[tooltipItem[0].datasetIndex]['label']+" : " + k_amount
                                                }
                                                else if (ks_selection === 'custom'){
                                                    var ks_field = ks_self.chart_data.ks_field;
                                                    k_amount =  formats.format_value(k_amount, { type: 'float', digits: [69, 2]})
                                                    return data.datasets[tooltipItem[0].datasetIndex]['label']+" : " + k_amount+" "+ ks_field;
                                                }
                                                else {
                                                    k_amount =  formats.format_value(k_amount, { type: 'float', digits: [69, 2]})
                                                    return data.datasets[tooltipItem[0].datasetIndex]['label']+" : " + k_amount
                                                }                                               },
                                           label : function(tooltipItem, data) {
                                                      return data.labels[tooltipItem.index];
                                                    },

                                             }
                for (var i = 0; i < datasets.length; i++) {
                    datasets[i].backgroundColor = chartColors;
                    datasets[i].borderColor = "rgba(255,255,255,1)";
                }
             if(semi_circle && (chartType === "pie" || chartType === "doughnut")){
                    options.rotation = 1*Math.PI;
                    options.circumference = 1*Math.PI;
                }
            } else if (ksChartFamily == "square") {
                options.scales.xAxes[0].gridLines.display = false;
                options.scales.yAxes[0].ticks.beginAtZero = true;
                options.plugins.datalabels.align = 'end';
                options.plugins.datalabels.formatter = function(value, ctx) {
                    var ks_self = self;
                    var ks_selection = ks_self.chart_data.ks_selection;
                    if (ks_selection === 'monetary'){
                        var ks_currency_id = ks_self.chart_data.ks_currency;
                        var ks_data = self.ksNumFormatter(value,1);
                        ks_data = self.ks_monetary(ks_data, ks_currency_id);
                        return ks_data;
                    }
                    else if (ks_selection === 'custom'){
                        var ks_field = ks_self.chart_data.ks_field;
                        return self.ksNumFormatter(value,1) +' '+ ks_field;
                    }
                    else {
                        return self.ksNumFormatter(value,1);
                    }
                };

            if(chartType==="line"){
                    options.plugins.datalabels.backgroundColor= function(context) {
                                    return context.dataset.borderColor;
                                };
                }

                if(chartType === "horizontalBar"){
                    options.scales.xAxes[0].ticks.callback = function(value,index,values){
                        var ks_self = self;
                        var ks_selection = ks_self.chart_data.ks_selection;
                        if (ks_selection === 'monetary'){
                            var ks_currency_id = ks_self.chart_data.ks_currency;
                            var ks_data = self.ksNumFormatter(value,1);
                            ks_data = self.ks_monetary(ks_data, ks_currency_id);
                            return ks_data;
                        }
                        else if (ks_selection === 'custom'){
                            var ks_field = ks_self.chart_data.ks_field;
                            return self.ksNumFormatter(value,1) +' '+ ks_field;
                        }
                        else{
                            return self.ksNumFormatter(value,1);
                        }
                    }
                    options.scales.xAxes[0].ticks.beginAtZero = true;
                }
                else{
                    options.scales.yAxes[0].ticks.callback = function(value,index,values){
                        var ks_self = self;
                        var ks_selection = ks_self.chart_data.ks_selection;
                        if (ks_selection === 'monetary'){
                            var ks_currency_id = ks_self.chart_data.ks_currency;
                            var ks_data = self.ksNumFormatter(value,1);
                            ks_data = self.ks_monetary(ks_data, ks_currency_id);
                            return ks_data;
                        }
                        else if (ks_selection === 'custom'){
                            var ks_field = ks_self.chart_data.ks_field;
                            return self.ksNumFormatter(value,1) +' '+ ks_field;
                        }
                        else{
                            return self.ksNumFormatter(value,1);
                        }
                    }
                }
                options.tooltips.callbacks = {
                    label: function(tooltipItem, data) {
                        var ks_self = self;
                        var k_amount = data.datasets[tooltipItem.datasetIndex]['data'][tooltipItem.index];
                        var ks_selection = ks_self.chart_data.ks_selection;
                        if (ks_selection === 'monetary'){
                            var ks_currency_id = ks_self.chart_data.ks_currency;
                            k_amount = self.ks_monetary(k_amount, ks_currency_id);
                            return data.datasets[tooltipItem.datasetIndex]['label']+" : " + k_amount
                        }
                        else if (ks_selection === 'custom'){
                            var ks_field = ks_self.chart_data.ks_field;
                            k_amount =  formats.format_value(k_amount, { type: 'float', digits: [69, 2]})
                            return data.datasets[tooltipItem.datasetIndex]['label']+" : " + k_amount+" "+ ks_field;
                        }
                        else {
                            k_amount =  formats.format_value(k_amount, { type: 'float', digits: [69, 2]})
                            return data.datasets[tooltipItem.datasetIndex]['label']+" : " + k_amount
                        }
                    }
                }
                for (var i = 0; i < datasets.length; i++) {
                    switch (ksChartType) {
                        case "bar":
                        case "horizontalBar":
                            if (datasets[i].type && datasets[i].type=="line"){
                                datasets[i].borderColor = chartColors[i];
                                datasets[i].backgroundColor = "rgba(255,255,255,0)";
                            } else {
                                datasets[i].backgroundColor = chartColors[i];
                                datasets[i].borderColor = "rgba(255,255,255,0)";
                                options.scales.xAxes[0].stacked = stack;
                                options.scales.yAxes[0].stacked = stack;
                            }
                            break;
                        case "line":
                            datasets[i].borderColor = chartColors[i];
                            datasets[i].backgroundColor = "rgba(255,255,255,0)";
                            break;
                        case "area":
                            datasets[i].borderColor = chartColors[i];
                            break;
                    }
                }

            }
            ksMyChart.update();
        },



    });

    core.form_widget_registry.add('ks_dashboard_graph_preview', KsGraphPreview);

    return {
        KsGraphPreview: KsGraphPreview,
    };

});

