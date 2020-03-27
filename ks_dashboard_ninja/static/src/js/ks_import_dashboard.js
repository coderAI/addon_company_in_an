odoo.define('ks_dashboard_ninja.import_button', function (require) {

"use strict";

var core = require('web.core');
var _t = core._t;
var Sidebar = require('web.Sidebar');
var ListView = require('web.ListView');
var crash_manager = require('web.crash_manager');
var framework = require('web.framework');
var Model = require('web.DataModel');
var QWeb = core.qweb;

    ListView.include({

     render_buttons: function($node) {
         this._super.apply(this, arguments);
        if (this.$buttons) {

            var import_button = this.$buttons.find('.ks_import_button');
            var import_input_button = this.$buttons.find('.ks_input_import_button');
            import_button.click(this.proxy('ks_import_button')) ;
            import_input_button.change(this.proxy('ksImportFileChange')) ;
            this.$buttons.appendTo($node);
        }
    },

        // TO hide odoo default import button (it is inserted in dom by other module)
        on_attach_callback : function(){
            var self = this;
            if(this.model == "ks_dashboard_ninja.board"){
               $('button.o_button_import').hide();
            }
        },

        // TO add custom dashboard export option under action button
        render_sidebar: function($node) {
        if(this.model != "ks_dashboard_ninja.board"){
            this._super.apply(this, arguments);
        }

        if (!this.sidebar && this.options.sidebar) {
            this.sidebar = new Sidebar(this, {editable: this.is_action_enabled('edit')});
            if (this.fields_view.toolbar) {
                this.sidebar.add_toolbar(this.fields_view.toolbar);
            }
            this.sidebar.add_items('other', _.compact(
            [
                 { label: _t("Export Dashboard"), callback: this.ks_dashboard_export.bind(this) },
                this.fields_view.fields.active && {label: _t("Archive"), callback: this.do_archive_selected},
                this.fields_view.fields.active && {label: _t("Unarchive"), callback: this.do_unarchive_selected},
                this.is_action_enabled('delete') && { label: _t('Delete'), callback: this.do_delete_selected }
            ]));

            $node = $node || this.options.$sidebar;
            this.sidebar.appendTo($node);

            // Hide the sidebar by default (it will be shown as soon as a record is selected)
            this.sidebar.do_hide();

        }
    },

        ks_dashboard_export: function(){
            this.ks_on_dashboard_export(this.get_selected_ids());
        },



        ks_on_dashboard_export: function (ids){
            var self = this;
            new Model("ks_dashboard_ninja.board").call('ks_dashboard_export',[JSON.stringify(ids)]).then(function(result){
                    var name = "dashboard_ninja";
                    var data = {
                        "header":name,
                        "dashboard_data":result,
                      }
                framework.blockUI();
                self.session.get_file({
                    url: '/ks_dashboard_ninja/export/dashboard_json',
                    data: {data:JSON.stringify(data)},
                    complete: framework.unblockUI,
                    error: crash_manager.rpc_error.bind(crash_manager),
                });
            })
         },

        ks_import_button: function (e) {
            var self = this;
            $('.ks_input_import_button').click();
        },

        ksImportFileChange : function(e){
            var self = this;
            var fileReader = new FileReader();
            fileReader.onload = function () {
                $('.ks_input_import_button').val('');
                new Model("ks_dashboard_ninja.board").call('ks_import_dashboard',[fileReader.result]).then(function (result) {
                        if (result==="Success") {
                            framework.blockUI();
                            location.reload();
                        }
                    });
            };
            fileReader.readAsText($('.ks_input_import_button').prop('files')[0]);
        },

        _updateButtons : function(mode){
            if(this.$buttons){
                if(mode==="edit") this.$buttons.find('.ks_import_button').hide();
                else if(mode==="readonly") this.$buttons.find('.ks_import_button').show();
                this._super.apply(this, arguments);
            }
        },
        do_delete:function(ids){
        var self = this;
        if (this.model ==="ks_dashboard_ninja.board"){
             if (!(ids.length && confirm(_t("Do you really want to remove these records?")))) {
                return;
            }

            return $.when(this.dataset.unlink(ids)).done(function () {
                _(ids).each(function (id) {
                    self.records.remove(self.records.get(id));
                });

            self.do_action('reload');
//            self.reload();

        });


        }else{ this._super.apply(this, arguments);
        }

        },


    });
    core.action_registry.add('ks_dashboard_ninja.import_button', ListView);
    return ListView;

});
