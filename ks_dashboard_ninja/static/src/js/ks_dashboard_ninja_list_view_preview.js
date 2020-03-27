odoo.define('ks_dashboard_ninja_pro_list.ks_dashboard_list_view_preview', function (require) {
    "use strict";


    var common = require('web.form_common');
    var core = require('web.core');
      var formats = require('web.formats');

    var QWeb = core.qweb;

    var KsListViewPreview = common.AbstractField.extend({




        start : function(){
//         this.field_manager.fields.ks_dashboard_item_type.on('change',this.field_manager.fields.ks_list_view_preview,this.preview_update);
//            this.field_manager.fields.ks_chart_data_count_type.on('change',this.field_manager.fields.ks_list_view_preview,this.preview_update);
//            this.field_manager.fields.ks_list_view_data.on('change',this.field_manager.fields.ks_list_view_preview,this.preview_update);
//            this.field_manager.fields.ks_list_view_fields.on('change',this.field_manager.fields.ks_list_view_preview,this.preview_update);
//            this.field_manager.fields.ks_chart_relation_groupby.on('change',this.field_manager.fields.ks_list_view_preview,this.preview_update);
//            this.field_manager.fields.ks_chart_date_groupby.on('change',this.field_manager.fields.ks_list_view_preview,this.preview_update);
//            this.field_manager.fields.ks_show_records.on('change',this.field_manager.fields.ks_show_records,this.preview_update);
           this.field_manager.on("view_content_has_changed", this, this.preview_update);
            return this._super();
        },

        preview_update : function(){
            this.render_value();
        },

        init: function (parent, state, params) {
            this._super.apply(this, arguments);
            this.state = {};
        },

        render_value: function () {
            this.$el.empty()
            var fields = this.view.get_fields_values();
            if (fields.ks_dashboard_item_type === 'ks_list_view') {
                if (fields.ks_list_view_type =='ungrouped')
            {

                if (fields.ks_list_view_fields.length !== 0) {
                    this.ksRenderListView()
                } else {
                    this.$el.append($('<div>').text("Select Fields to show in list view."));

                }
                } else if(fields.ks_dashboard_item_type === 'ks_list_view'){
                    if (fields.ks_list_view_type =='grouped'){
                     if(fields.ks_chart_relation_groupby && fields.ks_list_view_group_fields.count !== 0){
                        this.ksRenderListView()
                    }else {
                        this.$el.append($('<div>').text("Select Fields and Group By to show in list view"));
                    }
                    }

                }


            }
        },

        ksRenderListView: function () {

            var field = this.view.get_fields_values();
            var ks_list_view_name;
            var count =  field.ks_record_count;
            if (field.name) ks_list_view_name = field.name;
            else if (field.ks_model_name) ks_list_view_name = this.field_manager.fields.ks_model_id.display_value[field.ks_model_id];
            else ks_list_view_name = "Name";

            var list_view_data;
            if (field.ks_list_view_data) list_view_data = JSON.parse(field.ks_list_view_data);
            else list_view_data = false;
           if(list_view_data){
                for (var i = 0; i < list_view_data.data_rows.length; i++){
                    for (var j = 0; j < list_view_data.data_rows[0]["data"].length; j++){
                        if(typeof(list_view_data.data_rows[i].data[j]) === "number"){
                            list_view_data.data_rows[i].data[j]  = formats.format_value(list_view_data.data_rows[i].data[j], { type: 'float', digits: [69, 2]})
                        }
                    }
                }
            }

            if(field.ks_list_view_type === "ungrouped" && list_view_data){
                var index_data = list_view_data.date_index;
                for (var i = 0; i < index_data.length; i++){
                    for (var j = 0; j < list_view_data.data_rows.length; j++){
                        var index = index_data[i]
                        var date = list_view_data.data_rows[j]["data"][index]

                        if (date)list_view_data.data_rows[j]["data"][index] = formats.format_value(moment(new Date(date+" UTC")), {type:"datetime"}, {timezone: false});
                        else list_view_data.data_rows[j]["data"][index] = "";
                    }
                }
            }
            count = list_view_data && field.ks_list_view_type === "ungrouped" ? count - list_view_data.data_rows.length : false;
            count = count ? count <=0 ? false : count : false;
            var $listViewContainer = $(QWeb.render('ks_list_view_container', {
                ks_list_view_name: ks_list_view_name,
                list_view_data: list_view_data,
                ks_show_records: this.field_manager.fields.ks_show_records.get_value(),
                count: count,
            }));
            this.$el.append($listViewContainer);

        },

    });
    core.form_widget_registry.add('ks_dashboard_list_view_preview', KsListViewPreview);

    return {
        KsListViewPreview: KsListViewPreview,
    };

});