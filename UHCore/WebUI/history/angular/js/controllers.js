'use strict';

/* Controllers */

var historyApp = angular.module('historyApp', ['$strap.directives']);
  
historyApp.controller('EpisodesListCtrl', function EpisodesListCtrl($scope, $http) {
  $http.get('data/events/').success(function(data) {
    $scope.episodes = data;
    $scope.tagsValue = '0';
    $scope.ruleName = [];
    $scope.locationName = [];
  });

  $scope.tagsItems = [{ label: "memorable", value: "important" },{ label:"interesting", value: "interesting" },{ label:"unclear", value: "question" },{ label:"none", value: "0" }];
  $scope.orderProp = 'time.narrative';
  //$scope.ruleName = 'name';

  

  $scope.setRadioValue=function(radioVal){
    $scope.tagsValue=radioVal;
    //$scope.ruleName.push(even);
  }

  $scope.setTags=function(tags,event){//this function should set the tags on the database
    $scope.dao= new dataHelper();
    $scope.dao.setTags(event.id, tags);
    event.tags[0]=tags;
    //$scope.ruleName.push(event.name);
  }

  $scope.loadLocationName = function (e) {
    //$scope.ruleName.push(e);
    //add if it's not repeated
    if ($scope.locationName.indexOf(e)==-1) $scope.locationName.push(e);
  }


  $scope.loadRuleName = function (e) {
    //$scope.ruleName.push(e);
    //add if it's not repeated
    if ($scope.ruleName.indexOf(e)==-1) $scope.ruleName.push(e);
  }

  $scope.clear_eventquery = function() {
    $scope.eventquery="";
  }

  $scope.clear_locationquery = function() {
    $scope.locationquery="";
  }


});

historyApp.controller('ModalCtrl', function ($scope, $modal){
$scope.viaService = function() {
    // create the modal
    var modal = $modal({
      template: 'angular/js/app/modal.html',
      show: true,
      scope: $scope,
      persist: true,
      backdrop: 'static'
    });
$scope.parentController = function(dismiss) {
    console.warn(arguments);
    // do something
    dismiss();
    }
  }
});

historyApp.controller('TagsCtrl', function TagsCtrl($scope,$html){
  $http.post('data/tags/').success(function(data){
    $scope.tag=data;
  });
    
});
//historyControllers.controller('EpisodesDetailCtrl', ['$scope', '$routeParams',
//  function($scope, $routeParams) {
//    $scope.phoneId = $routeParams.phoneId;
//  }]);

function dataHelper() {
}

dataHelper.prototype = {
  setTags : function(historyId, tags) {
    var url = 'data/tags'
    var result = {};
    var obj = {
      'historyId' : historyId,
      'tags' : tags
    };
    $.ajax({
      url : url,
      data : JSON.stringify(obj),
      async : false,
      contentType : 'application/json',
      error : function(jqXHR, status, error) {
        result = {
          status : status,
          error : jqXHR.responseText
        };
      },
      success : function(data, status, jqXHR) {
        result = {
          status : status,
          data : data
        };
      },
      type : 'POST'
    });
  }
}
