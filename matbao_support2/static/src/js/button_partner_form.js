odoo.define('matbao_support2.button_partner_form', function (require) {
"use strict";

var widgets = require('web.form_widgets');
var core = require('web.core');
var Model = require('web.Model');
var data = require('web.data');
var _t = core._t;
var QWeb = core.qweb;


widgets.WidgetButton.include({
    
    on_click: function() {
         if(this.node.attrs.custom === "click_show_mobile"){
        	 if (this.field_manager !== undefined && this.field_manager.datarecord !== undefined && this.field_manager.datarecord.mobile !== undefined)
    		 {
    			 $('.hidden_mobile_form_res_partner_form').addClass('o_form_invisible');
    			 $('.showed_mobile_form_res_partner_form').removeClass('o_form_invisible');
    			 $('.btn_hide_mobile_from_support').removeClass('o_form_invisible');
    			 $('.btn_show_mobile_from_support').addClass('o_form_invisible');
    			 var id = this.field_manager.datarecord.id
    			 new Model("res.partner").call("save_view_mobile_stories", [id]).then(function(result) {});
    		 }
        	 return;
         }
         if(this.node.attrs.custom === "click_hide_mobile"){
        	 if (this.field_manager !== undefined && this.field_manager.datarecord !== undefined && this.field_manager.datarecord.mobile !== undefined)
    		 {
        		 $('.hidden_mobile_form_res_partner_form').removeClass('o_form_invisible');
    			 $('.showed_mobile_form_res_partner_form').addClass('o_form_invisible');
    			 $('.btn_show_mobile_from_support').removeClass('o_form_invisible');
    			 $('.btn_hide_mobile_from_support').addClass('o_form_invisible');
    		 }
        	 return;
         }
         if(this.node.attrs.custom === "click_show_email"){
        	 if (this.field_manager !== undefined && this.field_manager.datarecord !== undefined && this.field_manager.datarecord.email !== undefined)
    		 {
    			 $('.hidden_email_form_res_partner_form').addClass('o_form_invisible');
    			 $('.showed_email_form_res_partner_form').removeClass('o_form_invisible');
    			 $('.btn_hide_email_from_support').removeClass('o_form_invisible');
    			 $('.btn_show_email_from_support').addClass('o_form_invisible');
    			 var id = this.field_manager.datarecord.id
    			 new Model("res.partner").call("save_view_email_stories", [id]).then(function(result) {}); 
    		 }
        	 return;
         }
         if(this.node.attrs.custom === "click_hide_email"){
        	 if (this.field_manager !== undefined && this.field_manager.datarecord !== undefined && this.field_manager.datarecord.email !== undefined)
    		 {
        		 $('.hidden_email_form_res_partner_form').removeClass('o_form_invisible');
    			 $('.showed_email_form_res_partner_form').addClass('o_form_invisible');
    			 $('.btn_show_email_from_support').removeClass('o_form_invisible');
    			 $('.btn_hide_email_from_support').addClass('o_form_invisible');
    		 }
        	 return;
         }
         if(this.node.attrs.custom === "click_show_email_wizard"){
        	 if (this.field_manager !== undefined && this.field_manager.datarecord !== undefined && this.field_manager.datarecord.email !== undefined){
        		 $('.hidden_email_form_res_partner_form_wizard').addClass('o_form_invisible');
    			 $('.showed_email_form_res_partner_form_wizard').removeClass('o_form_invisible');
    			 $('.btn_hide_email_from_support_wizard').removeClass('o_form_invisible');
    			 $('.btn_show_email_from_support_wizard').addClass('o_form_invisible');
    			 var type = this.field_manager.datarecord.type
    			 var parent_id = this.field_manager.datarecord.parent_id[0]
    			 new Model("res.partner").call("save_view_email_stories_wizard", [type, parent_id]).then(function(result) {}); 
         	}
        	return;
         }
         if(this.node.attrs.custom === "click_hide_email_wizard"){
        	 if (this.field_manager !== undefined && this.field_manager.datarecord !== undefined && this.field_manager.datarecord.email !== undefined){
    	    	 $('.hidden_email_form_res_partner_form_wizard').removeClass('o_form_invisible');
    			 $('.showed_email_form_res_partner_form_wizard').addClass('o_form_invisible');
    			 $('.btn_show_email_from_support_wizard').removeClass('o_form_invisible');
    			 $('.btn_hide_email_from_support_wizard').addClass('o_form_invisible');
         	}
        	return;
         }
         if(this.node.attrs.custom === "click_show_mobile_wizard"){
        	 if (this.field_manager !== undefined && this.field_manager.datarecord !== undefined && this.field_manager.datarecord.mobile !== undefined){
        		 $('.hidden_mobile_form_res_partner_form_wizard').addClass('o_form_invisible');
    			 $('.showed_mobile_form_res_partner_form_wizard').removeClass('o_form_invisible');
    			 $('.btn_hide_mobile_from_support_wizard').removeClass('o_form_invisible');
    			 $('.btn_show_mobile_from_support_wizard').addClass('o_form_invisible');
    			 var type = this.field_manager.datarecord.type
    			 var parent_id = this.field_manager.datarecord.parent_id[0]
    			 new Model("res.partner").call("save_view_mobile_stories_wizard", [type, parent_id]).then(function(result) {}); 
        	 }
        	 return;
 		 }
         if(this.node.attrs.custom === "click_hide_mobile_wizard"){
        	 if (this.field_manager !== undefined && this.field_manager.datarecord !== undefined && this.field_manager.datarecord.mobile !== undefined){
		    	 $('.hidden_mobile_form_res_partner_form_wizard').removeClass('o_form_invisible');
				 $('.showed_mobile_form_res_partner_form_wizard').addClass('o_form_invisible');
				 $('.btn_show_mobile_from_support_wizard').removeClass('o_form_invisible');
    			 $('.btn_hide_mobile_from_support_wizard').addClass('o_form_invisible');
        	 }
        	 return;
 		 }
        	 
         this._super();
    },
});

});

