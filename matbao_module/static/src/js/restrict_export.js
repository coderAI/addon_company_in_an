openerp.matbao_module = function(instance){    
	var _t = instance.web._t;
		instance.web.Sidebar.include({        
		add_items: function(section_code, items) {
			var self = this;        	
			var _super = self._super;        	
			var args = arguments;
			var model = this.__parentedParent.model
			var no_export_model = ['sale.order', 'res.partner', 'sale.service']
			var Users = new instance.web.Model('res.users');
			Users.call('has_group', ['matbao_module.export_data_group']).done(function(is_employee) {
				if(is_employee || no_export_model.indexOf(model) < 0){
					_super.apply(self, args);
				} else{
					var export_label = _t("Export"); 
					var new_items = items;
					if (section_code == 'other') {
						new_items = [];
						for (var i = 0; i < items.length; i++) {
							console.log("items[i]: ", items[i]);
							if (items[i]['label'] != export_label) {
								new_items.push(items[i]);
							};
						};
					};
					if (new_items.length > 0) {
						_super.call(self, section_code, new_items);
					};
				}
			});
		},
	});
};
