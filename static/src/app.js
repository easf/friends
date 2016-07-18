/* App main file */
$(document).ready(function(){
  
  // This piece of code is just to replicate the html
  // var tmpl = $(".friends").html();
  // $(".friends").html("");
  // for (var i=0; i<20; i++){
  //   var friend = tmpl.replace(/user\['id'\]/g, i);
  //   $(".friends").append($.parseHTML(friend));
  // }
  
  
  // This is to keep a score of number of items completed
  var N_QUESTIONS = 4;
  $(".score .label").html(0);
  $(".friend input[type=radio]").change(function(e){
     
    var ncompleted = 0;
    $(".friend").each(function(){
      var list = $(this).find(".feedback:has(input:checked)");
      if (list.length==N_QUESTIONS){
          ncompleted++;
      }
    });
    if ($(".score .label").text() != ncompleted){
      $(".score .label").html(ncompleted);
      $(".score .label").animate({ fontSize: "1.5em",  }, 500 )
                        .animate({ fontSize: "1em" }, 500 );
    }
  });  

 function loading (){
     $('#ranking').hide();
     $('#loading-image').show();
     return true;
  } 

});

 