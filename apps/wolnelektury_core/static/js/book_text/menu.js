(function($){$(function(){


function hide_menu_boxes() {
    /* Closes any open menu boxes. */
    $("#menu .active").each(function() {
        $(this).removeClass("active");
        $("#" + $(this).attr("data-box")).hide();
    });
    $("#box-underlay").hide();
}

function release_menu() {
    /* Exits the menu. It only really disappears on small screens. */
    hide_menu_boxes();
    $("body").removeClass("menu-showed");
}

/* Show menu */
$('#menu-toggle-on').click(function(e) {
    e.preventDefault();
    var body = $("body");
    /* Just stop hiding the menu. This way, after narrowing the browser,
     * menu will still disappear normally. */
    body.removeClass("menu-hidden");
    /* Menu still not visible? Really open it then. */
    if (!$("#menu").is(":visible")) {
        body.addClass("menu-showed");
    }
});

/* Hide menu */
$('#menu-toggle-off').click(function(e) {
    e.preventDefault();
    /* Just release the menu. This way, after widening the browser,
     * menu will still appear normally. */
    release_menu();
    /* Menu still visible after releasing it? Really hide it then. */
    if ($("#menu").is(":visible")) {
        $("body").addClass("menu-hidden");
    }
});


/* Exit menu by clicking anywhere else. */
$("#box-underlay").click(release_menu);


/* Toggle hidden box on click. */
$("#menu a").each(function() {
    var boxid = $(this).attr("data-box");
    if (boxid) {
        $("#" + $(this).attr("data-box")).hide();

        $(this).click(function(e) {
            e.preventDefault();
            var showing = $(this).hasClass("active");
            hide_menu_boxes();
            if (!showing) {
                $("body").addClass("menu-showed");
                $(this).addClass("active");
                $("#box-underlay").show();
                $("#" + $(this).attr("data-box")).show();
            }
        });
    }
    else {
        $(this).click(release_menu);
    }
});


/* Show menu item for other versions of text. 
 * It's only present if there are any. */
$("#menu-other").show();


/* Load other version of text. */
$(".display-other").click(function(e) {
    e.preventDefault();
    release_menu();

    $("#other-text").show();
    $("body").addClass('with-other-text');

    $.ajax($(this).attr('data-other'), {
        success: function(text) {
            $("#other-text-body").html(text);
            $("#other-text-waiter").hide();
            $("#other-text-body").show();
            loaded_text($("#other-text-body"));
        }
    });
});


/* Remove other version of text. */
$(".other-text-close").click(function(e) {
    release_menu();
    e.preventDefault();
    $("#other-text").hide();
    $("body").removeClass('with-other-text');
    $("#other-text-body").html("");
});


/* Release menu after clicking inside TOC. */
$("#toc a").click(release_menu);


if ($('#nota_red').length > 0) {
    $("#menu-nota_red").show();
}

/* Show themes menu item, if there are any. */
if ($('#themes li').length > 0) {
    $("#menu-themes").show();
}

function loaded_text(text) {
    /* Attach events to elements inside book texts here.
     * This way they'll work for the other text when it's loaded. */

    $(".theme-begin", text).click(function(e) {
        e.preventDefault();
        if ($(this).css("overflow") == "hidden" || $(this).hasClass('showing')) {
            $(this).toggleClass("showing");
        }
    });

}
loaded_text("#book-text");


})})(jQuery);
