odoo.define('matbao_support2.res_partner', function(require)
{
    'use strict';
    var core = require('web.core');
    var FormView = require('web.FormView');

    FormView.include({
	    
	    update_pager: function() {
	        if (this.pager) {
	        	if (this.model !== undefined && this.model === 'res.partner'){
	        		if ($('.showed_mobile_form_res_partner_form').is(":visible")){
	        			$('.hidden_mobile_form_res_partner_form').removeClass('o_form_invisible');
		   			 	$('.showed_mobile_form_res_partner_form').addClass('o_form_invisible');
	        		}
	        		
	   			 	if ($('.btn_hide_mobile_from_support').is(":visible")){
		   			 	$('.btn_hide_mobile_from_support').addClass('o_form_invisible');
		    			$('.btn_show_mobile_from_support').removeClass('o_form_invisible');
	   			 	}
	   			 	
	   			 	if ($('.showed_email_form_res_partner_form').is(":visible")){
	        			$('.hidden_email_form_res_partner_form').removeClass('o_form_invisible');
		   			 	$('.showed_email_form_res_partner_form').addClass('o_form_invisible');
	        		}
	        		
	   			 	if ($('.btn_hide_email_from_support').is(":visible")){
		   			 	$('.btn_hide_email_from_support').addClass('o_form_invisible');
		    			$('.btn_show_email_from_support').removeClass('o_form_invisible');
	   			 	}
		    	}
	        	
	        }
	        return this._super();
	    },
	    
	    to_edit_mode: function() {
	    	if (this.model !== undefined && this.model === 'res.partner'){
	    		
	    		if ($('.showed_mobile_form_res_partner_form').is(":visible")){
        			$('.hidden_mobile_form_res_partner_form').removeClass('o_form_invisible');
	   			 	$('.showed_mobile_form_res_partner_form').addClass('o_form_invisible');
        		}
	    		
	    		if ($('.showed_email_form_res_partner_form').is(":visible")){
        			$('.hidden_email_form_res_partner_form').removeClass('o_form_invisible');
	   			 	$('.showed_email_form_res_partner_form').addClass('o_form_invisible');
        		}
	    		
		    	if ($('.btn_hide_mobile_from_support').is(":visible")){
	   			 	$('.btn_hide_mobile_from_support').addClass('o_form_invisible');
	    			$('.btn_show_mobile_from_support').removeClass('o_form_invisible');
				}
		    	if ($('.btn_hide_email_from_support').is(":visible")){
	   			 	$('.btn_hide_email_from_support').addClass('o_form_invisible');
	    			$('.btn_show_email_from_support').removeClass('o_form_invisible');
				}
	    	}
	    	return this._super();
	    },
    });

});
