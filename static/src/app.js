/* App main file */
$(document).ready(function(){
  
  // This piece of code is just to replicate the html
  // var tmpl = $(".friends").html();
  // $(".friends").html("");
  // xx`
  //   var friend = tmpl.replace(/user\['id'\]/g, i);
  //   $(".friends").append($.parseHTML(friend));
  // }
  
  
  // This is to keep a score of number of items completed
  $(".score .label").html(0);
  $(".friend input[type=radio]").change(function(e){
    var N_QUESTIONS = 4; 
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
  
  
  $(".close-friends .friend input[type=checkbox]").change(function(e){
   var N_QUESTIONS = 3;  
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

  $("#consentCheck").change(function(){
      $("#ranking").toggleClass("disabled");
      
      if($("#consentCheck").is(":checked")){
        $("#consentCheck").parent().removeClass("text-danger");
      }
      
  });

  $("#ranking").click(function(e){

      if($(this).hasClass("disabled")) {
        $("#consentCheck").parent().addClass("text-danger");
        return;
      } 

      FB.login(function(response){
        checkLoginState();       
      },{ scope: "public_profile, user_work_history, user_education_history, user_hometown, user_location,"+
                 " user_friends, user_likes, user_posts, user_relationships, user_relationship_details,"+
                 " user_religion_politics, user_birthday"});
    
  });


});




 