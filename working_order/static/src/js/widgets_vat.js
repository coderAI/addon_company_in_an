odoo.define('working_order.form_widgets_vat', function (require) {
	"use strict";
	var core = require('web.core');
	var Model = require('web.Model');
	var _t = core._t;
	var QWeb = core.qweb;
	var FieldMany2Many = core.form_widget_registry.get('many2many');
	var FormView = require('web.FormView');

	FormView.include({

	    load_record: function(record){
	    	this._super(record);
	    	// debugger;
	    	if (this.model !== undefined && this.model === 'loading.sale.order'){
	    		console.log(this);
	    		if (this.datarecord && this.datarecord.sale_order_line_ids && this.datarecord.sale_order_line_ids.length > 0) {
	    			if (this.$el.find(".ep_button_delete") && this.$el.find(".ep_button_delete").length > 0) {
	    				this.$el.find(".ep_button_delete").css({"display":""});
					}
	    			else {
	    				this.$el.find(".o_x2m_control_panel").after('<div><button icon="gtk-yes" style="margin-top:5px; margin-bottom:5px;" class="ep_button_delete btn btn-sm btn-primary btn-default" href="javascript:void(0)">Delete</button></div>');
					}
				}
				else {
	    			this.$el.find(".ep_button_delete").css({"display":"none"});
				}
	    	}
	        // return this._super(record);
	    }
    });

	var X2ManySelectableInvoiceLines = FieldMany2Many.extend({
		multi_selection: true,
		init: function() {
			this._super.apply(this, arguments);
		},
		start: function()
		{
			this._super.apply(this, arguments);
			var self=this;
			console.log(this, this._ic_field_manager.dataset.context);
			this.$el.prepend(QWeb.render("X2ManySelectableInvoiceLines", {widget: this}));
			if (this._ic_field_manager.model === 'loading.sale.order') {
				this.$el.find(".ep_button_delete").css({"display":"none"});
			}
			else {
				this.$el.find(".ep_button_confirm").css({"display":"none"});
				if (this._ic_field_manager && this._ic_field_manager.datarecord.state !== 'new') {

					this.$el.find(".ep_button_delete").css({"display": "none"});
				}
                var Users =new Model('res.users');
                Users.call('has_group', ['account.group_account_invoice']).done(function(is_accountant) {
                    if (!is_accountant) {
                        self.$el.find(".ep_button_delete").css({"display": "none"});
                    }
                })
			}
			this.$el.find(".ep_button_confirm").click(function(){
				self.action_selected_lines();
			});
			this.$el.find(".ep_button_delete").click(function(){
				var result = confirm("Do you really want to delete?");
				if (result) {
					self.action_selected_lines_to_delete();
				}
			});
	    },

	    action_selected_lines: function()
	    {
			debugger;
			var self = this;
			var selected_ids = self.get_selected_ids_one2many();
			if (selected_ids.length === 0)
			{
				this.do_warn(_t("You must choose at least one record."));
				return false;
			}
			var model_obj=new Model(this.dataset.model); //you can hardcode model name as: new Model("module.model_name");
			//you can change the function name below
			model_obj.call('get_invoice_lines_to_export_vat',[selected_ids],{context:self._ic_field_manager.dataset.context}).done(function () {
				self.do_action('reload');
			});
	    },

	    action_selected_lines_to_delete: function()
	    {
			debugger;
			var self = this;
			var export_id = self._ic_field_manager.datarecord.id;
			var selected_ids = self.get_selected_ids_one2many();
			if (selected_ids.length === 0)
			{
				this.do_warn(_t("You must choose at least one record."));
				return false;
			}
			var model_obj=new Model(this.dataset.model); //you can hardcode model name as: new Model("module.model_name");
			//you can change the function name below
			model_obj.call('unlink_invoice_from_export',[selected_ids, export_id],{context:self._ic_field_manager.dataset.context}).done(function (result) {
				if (result && result.code === 0){
					alert(result.msg);
				}
				else {self.do_action('reload');}
			});
	    },
	    get_selected_ids_one2many: function ()
	    {
		   var ids =[];
		   this.$el.find('input[name="radiogroup"]').filter(":checked")
				   .closest('tr').each(function () {
					ids.push(parseInt($(this).context.dataset.id));
		   });
		   return ids;
	    },
	});
	core.form_widget_registry.add('x2many_get_invoice_lines_to_export', X2ManySelectableInvoiceLines);
	return X2ManySelectableInvoiceLines;
});
