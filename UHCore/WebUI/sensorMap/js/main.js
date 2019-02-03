Function.prototype.bind = function(scope) {
  var _function = this;
  
  return function() {
    return _function.apply(scope, arguments);
  }
}

function uiHelper() {
}

uiHelper.prototype = {
	load : function(img) {
		this.autoRefresh(img);
	},

	autoRefresh : function(img) {
		var self = this;
		setTimeout(function() {
			$(img).attr("src", "image");
			//doing this causes a massive memory leak
			//since the image is an svg, it should be fine without cache busting
			$(img).attr("src", "image?cachebust=" + new Date().getTime());
			self.autoRefresh(img);
		}, 2000);
	},
}

function dataHelper() {
}

dataHelper.prototype = {
	getResponses : function() {
		var responses = null;
		$.ajax({
			url : '../details/data',
			dataType : 'json',
			async : false,
			timeout: 3000,
			success : function(data, textStatus, jqXHR) {
				responses = data
			},
		});

		return responses;
	},

	pollResponses : function(callback, root) {
		var self = this;
		var data = self.getResponses();
		callback(root, data);
		setTimeout(function() {
			self.pollResponses(callback, root);
		}, 2000);
	},
}


function itemHelper() {
}

itemHelper.prototype = {
  load : function(targetDiv) {
		var dao = new dataHelper();
		dao.pollResponses(this.fill.bind(this), targetDiv);
	},
  
  fill : function(root, data) {
		$(root).empty();
    var id = 0;
    for(key in data){
      var channel = data[key];
      var container = $('<a></a>');
      $(root).append(container);
      $(container).attr("class", "area");
      $(container).attr("id", id);
      $(container).css('background-color', channel['color']);
      $(container).css('left', (window.innerWidth/2 + parseFloat(channel['x']) * 75 - 130) + "px");
      $(container).css('top', (window.innerHeight/2 - parseFloat(channel['y']) * 78 - 280) + "px");

      var head = $('<p></p>');
      $(container).append(head);
      $(container).append(channel['status'] + " (" + channel['value'] + ")");
      $(head).text(channel['name']);
      id = id + 1;
    }
//     var id = 0;
//     var flag = false;
//     for(key in data) {
//       var channel = data[key];
//       var cnt = $('#' + id);
//       cnt.bind('touchstart', function(){
//         if (!flag) {
//           flag = true;
//           setTimeout(function(){ flag = false; }, 2000);
//         cnt.toggleClass('show-nav');
//         }
//         return false
//       });
// 
//       cnt.hover(function(){
//         cnt.addClass('show-nav');
//         }, function(){
//         cnt.removeClass('show-nav');	
//       });
//       id = id + 1;
//     }
	},
}
