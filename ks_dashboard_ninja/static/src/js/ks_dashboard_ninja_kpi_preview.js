odoo.define('ks_dashboard_ninja_list.ks_dashboard_kpi_preview', function (require) {
    "use strict";

    var core = require('web.core');
    var common = require('web.form_common');

    var core = require('web.core');

    var formats = require('web.formats');
    var session = require('web.session');
    var utils = require('web.utils');

    var Qweb = core.qweb;

    var KsKpiPreview = common.AbstractField.extend({

         start: function() {
            this.field_manager.fields.ks_data_comparison.on('change',this.field_manager.fields.ks_kpi_preview,this.preview_update);
            this.field_manager.fields.ks_kpi_data.on('change',this.field_manager.fields.ks_kpi_preview,this.preview_update);
            this.field_manager.fields.ks_layout.on('change',this.field_manager.fields.ks_kpi_preview,this.preview_update);
            this.field_manager.fields.name.on('change',this.field_manager.fields.ks_kpi_preview,this.preview_update);
            this.field_manager.fields.ks_record_count.on('change',this.field_manager.fields.ks_kpi_preview,this.preview_update);
//            this.field_manager.fields.ks_model_id.on('change',this.field_manager.fields.ks_kpi_preview,this.preview_update);
            this.field_manager.fields.ks_domain.on('change',this.field_manager.fields.ks_kpi_preview,this.preview_update);
            this.field_manager.fields.ks_icon_select.on('change',this.field_manager.fields.ks_kpi_preview,this.preview_update);
            this.field_manager.fields.ks_icon.on('change',this.field_manager.fields.ks_kpi_preview,this.preview_update);
            this.field_manager.fields.ks_background_color.on('change',this.field_manager.fields.ks_kpi_preview,this.preview_update);
            this.field_manager.fields.ks_font_color.on('change',this.field_manager.fields.ks_kpi_preview,this.preview_update);
            this.field_manager.fields.ks_default_icon_color.on('change',this.field_manager.fields.ks_kpi_preview,this.preview_update);
            this.field_manager.fields.ks_default_icon.on('change',this.field_manager.fields.ks_kpi_preview,this.preview_update);
            this.field_manager.fields.ks_target_view.on('change',this.field_manager.fields.ks_kpi_preview,this.preview_update);
            return this._super();
        },

        preview_update : function(e){
                this.render_value();
        },

        file_type_magic_word: {
            '/': 'jpg',
            'R': 'gif',
            'i': 'png',
            'P': 'svg+xml',
        },

        //        Number Formatter into shorthand function
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

        render_value: function () {
            this.$el.empty();
            var field = this.view.get_fields_values();
            if(field.ks_model_id && field.ks_dashboard_item_type === "ks_kpi"){
                if(!field.ks_model_id_2 ){
                    if(!(field.ks_record_count_type === 'count')){
                        if(field.ks_record_field){
                            this.renderKpi();
                        }else{
                            this.$el.append("Select a Record field ")
                        }
                    }
                    else{
                      this.renderKpi();
                    }
                }
                else{
                    if(!(field.ks_record_count_type_2 === 'count') && !(field.ks_record_count_type === 'count')){
                        if(field.ks_record_field_2 && field.ks_record_field){
                            this.renderKpi();
                        }else{
                            this.$el.append("Select a Record fields ")
                        }
                    }
                    else if(!(field.ks_record_count_type_2 === 'count') && (field.ks_record_count_type === 'count')){
                        if(field.ks_record_field_2){
                            this.renderKpi();
                        }else{
                            this.$el.append("Select a Record field")
                        }
                    }
                    else if((field.ks_record_count_type_2 === 'count') && !(field.ks_record_count_type === 'count')){
                        if(field.ks_record_field){
                            this.renderKpi();
                        }else{
                            this.$el.append("Select a Record field")
                        }
                    }
                    else{
                        this.renderKpi();
                    }
                }
            }else {
                this.$el.append("Select a Model first")
            }
        },

            renderKpi: function(){
            var self = this;
            var field = self.view.get_fields_values();
            if (field.ks_kpi_data){
                var kpi_data = JSON.parse(field.ks_kpi_data);
                var count_1 = kpi_data[0]['record_data'];
                var count_2 = kpi_data[1]?kpi_data[1].record_data: undefined;
                var target_1 = kpi_data[0].target;
                var ks_valid_date_selection = ['l_day','t_week','t_month','t_quarter','t_year'];
                var target_view = field.ks_target_view,
                    pre_view =  field.ks_prev_view;
                var ks_rgba_background_color = self._get_rgba_format(field.ks_background_color);
                var ks_rgba_font_color = self._get_rgba_format(field.ks_font_color)
                if(field.ks_goal_enable){
                    var diffrence = 0.0
                    diffrence = count_1 - target_1
                    var acheive = diffrence>=0 ? true : false;
                    diffrence =  Math.abs(diffrence);
                    var deviation = Math.round((diffrence/target_1)*100)
                    if (deviation!==Infinity)  deviation = deviation? deviation + '%' : 0 + '%';
                }
                if(field.ks_previous_period && ks_valid_date_selection.indexOf(field.ks_date_filter_selection)>=0){
                    var previous_period_data = kpi_data[0].previous_period;
                    var pre_diffrence = (count_1 - previous_period_data);
                    var pre_acheive = pre_diffrence>0 ? true : false;
                    pre_diffrence = Math.abs(pre_diffrence);
                    var pre_deviation = previous_period_data ? parseInt((pre_diffrence/previous_period_data)*100) + '%' : "100%"
                }

                var ks_rgba_icon_color = self._get_rgba_format(field.ks_default_icon_color)

                var item_info = {
                    count_1 : self.ksNumFormatter(kpi_data[0]['record_data'], 1),
                    count_1_tooltip: kpi_data[0]['record_data'],
                    count_2 : kpi_data[1] ? String(kpi_data[1]):false ,
                    name : field.name ? field.name : this.field_manager.fields.ks_model_id['display_value'][this.view.get_fields_values().ks_model_id],
                    target_progress_deviation : String(Math.round((count_1/target_1)*100)),
                    icon_select : field.ks_icon_select,
                    default_icon: field.ks_default_icon,
                    icon_color: ks_rgba_icon_color,
                    target_deviation: deviation,
                    target_arrow: acheive ? 'up':'down',
                    ks_enable_goal: field.ks_goal_enable,
                    ks_previous_period: ks_valid_date_selection.indexOf(field.ks_date_filter_selection)>=0 ? field.ks_previous_period:false,
                    target: self.ksNumFormatter(target_1, 1),
                    target_tooltip: target_1,
                    previous_period_data: previous_period_data,
                    pre_deviation: pre_deviation,
                    pre_arrow : pre_acheive ? 'up':'down',
                    target_view : field.ks_target_view,
                }

                if (item_info.target_deviation===Infinity) item_info.target_arrow = false;
                item_info.target_progress_deviation = parseInt(item_info.target_progress_deviation)?item_info.target_progress_deviation:"0"
                if (field.ks_icon) {
                    if (!utils.is_bin_size(field.ks_icon)) {
                        // Use magic-word technique for detecting image type
                        item_info['img_src'] = 'data:image/' + (self.file_type_magic_word[field.ks_icon[0]] || 'png') + ';base64,' + field.ks_icon;
                    } else {
                        item_info['img_src'] = session.url('/web/image', {
                            model: self.view.dataset.model,
                            id: JSON.stringify(self.view.datarecord.id || null),
                            field: (this.field_manager.fields.ks_icon.options.preview_image)? this.field_manager.fields.ks_icon.options.preview_image : this.field_manager.fields.ks_icon.name,
                            unique: (this.field_manager.fields.ks_icon.view.datarecord.__last_update || '').replace(/[^0-9]/g, ''),
                        });
                    }
                }

                var $kpi_preview;
                if(!kpi_data[1]){
                    if(target_view ==="Number" || !field.ks_goal_enable) {
                        $kpi_preview = $(Qweb.render("ks_kpi_preview_template",item_info));
                    }
                    else if (target_view === "Progress Bar" && field.ks_goal_enable){
                        $kpi_preview = $(Qweb.render("ks_kpi_preview_template_3",item_info));
                        $kpi_preview.find('#ks_progressbar').val(parseInt(item_info.target_progress_deviation));
                    }

                    if(field.ks_goal_enable){
                        if(acheive){
                            $kpi_preview.find(".target_deviation").css({
                                "color" : "green",
                            });
                        }else{
                          $kpi_preview.find(".target_deviation").css({
                                "color" : "red",
                            });
                        }
                    }
                    if(field.ks_previous_period && String(previous_period_data) && ks_valid_date_selection.indexOf(field.ks_date_filter_selection)>=0){
                        if(pre_acheive){
                            $kpi_preview.find(".pre_deviation").css({
                                "color" : "green",
                            });
                        }else{
                          $kpi_preview.find(".pre_deviation").css({
                                "color" : "red",
                            });
                        }
                    }
                    if($kpi_preview.find('.row').children().length !== 2){
                        $kpi_preview.find('.row').children().addClass('ks_text-center');
                    }
                }
                else{
                    switch(field.ks_data_comparison){
                        case "None":
                            var count_tooltip = String(count_1)+"/"+String(count_2);
                            var count = String(self.ksNumFormatter(count_1))+"/"+String(self.ksNumFormatter(count_2));
                            item_info['count'] = count;
                            item_info['count_tooltip'] = count_tooltip;
                            item_info['target_enable'] = false;
                             $kpi_preview = $(Qweb.render("ks_kpi_preview_template_2",item_info));
                            break;
                        case "Sum":
                            var count = count_1 + count_2
                            item_info['count'] = self.ksNumFormatter(count, 1);
                            item_info['count_tooltip'] = count;
                            item_info['target_enable'] = true;
                            var ks_color = (target_1-count)>0? "red" : "green";
                            item_info.pre_arrow = (target_1-count)>0? "down" : "up";
                            item_info['ks_comparison'] = true;
                            var target_deviation = (target_1-count)>0? Math.round(((target_1-count)/target_1)*100) : Math.round((Math.abs((target_1-count))/target_1)*100);
                            if (target_deviation!==Infinity)  item_info.target_deviation = target_deviation + "%";
                            else {
                                item_info.pre_arrow = false;
                                item_info.target_deviation = target_deviation;
                            }
                            var target_progress_deviation = target_deviation && target_deviation !== Infinity ? Math.abs((100 - target_deviation)) : 0
                            item_info.target_progress_deviation = target_progress_deviation + "%";
                            $kpi_preview = $(Qweb.render("ks_kpi_preview_template_2",item_info));
                            $kpi_preview.find('.target_deviation').css({
                                "color":ks_color
                            });
                            if(field.ks_target_view === "Progress Bar"){
                                $kpi_preview.find('#ks_progressbar').val(target_progress_deviation)
                            }
                            break;
                       case "Percentage":
                        var count = parseInt((count_1/count_2)*100);
                        if(!count) count = 0;

                        item_info['count'] = count ? formats.format_value(count, { type: 'integer'})+"%" : "0%";
                        item_info['count_tooltip'] = count ? count+"%" : "0%";
                        item_info.target_progress_deviation = item_info['count']
                        target_1 = target_1 > 100 ? 100 : target_1;
                        item_info.target = target_1 + "%";
                        item_info.target_tooltip = target_1 + "%";
                        item_info.pre_arrow = (target_1-count)>0? "down" : "up";
                        var ks_color = (target_1-count)>0? "red" : "green";
                        item_info['target_enable'] = field.ks_goal_enable;
                        item_info['ks_comparison'] = false;
                        item_info.target_deviation = item_info.target > 100 ? 100 : item_info.target;
                         $kpi_preview = $(Qweb.render("ks_kpi_preview_template_2",item_info));
                         $kpi_preview = $(Qweb.render("ks_kpi_preview_template_2",item_info));
                        $kpi_preview.find('.target_deviation').css({
                            "color":ks_color
                        });
                            if(field.ks_target_view === "Progress Bar"){
                                $kpi_preview.find('#ks_progressbar').val(count)
                            }
                            break;
                        case "Ratio":
                            var gcd = self.ks_get_gcd(Math.round(count_1),Math.round(count_2));
                            if(count_1 && count_2){
                                item_info['count_tooltip'] =  count_1/gcd + ":" + count_2/gcd;
                                item_info['count'] = self.ksNumFormatter(count_1/gcd, 1) + ":" + self.ksNumFormatter(count_2/gcd, 1);
                            }else{
                                item_info['count_tooltip'] = count_1 + ":" +count_2;
                                item_info['count'] = self.ksNumFormatter(count_1, 1) + ":" + self.ksNumFormatter(count_2, 1);
                            }
                            item_info['target_enable'] = false;
                             $kpi_preview = $(Qweb.render("ks_kpi_preview_template_2",item_info));
                            break;
                    }
                }
                $kpi_preview.css({
                    "background-color" : ks_rgba_background_color,
                    "color":ks_rgba_font_color,
                });
                this.$el.append($kpi_preview);
            }

        },


        ks_get_gcd : function(a, b) {
            return (b == 0) ? a : this.ks_get_gcd(b, a%b);
        },

        _get_rgba_format: function (val) {
            var rgba = val.split(',')[0].match(/[A-Za-z0-9]{2}/g);
            rgba = rgba.map(function (v) {
                return parseInt(v, 16)
            }).join(",");
            return "rgba(" + rgba + "," + val.split(',')[1] + ")";
        }

    });
    core.form_widget_registry.add('ks_dashboard_kpi_preview', KsKpiPreview);
    return {
        KsKpiPreview: KsKpiPreview
    };

});

