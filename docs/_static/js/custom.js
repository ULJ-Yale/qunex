window.addEventListener('load', function() {
/*
    The jQuery script below extracts image descriptions that are "hidden" into
    the alt attribute by the myst_parser Sphinx extension and makes them visible
    by appending them to the parent paragraphs (just like they appear in the
    BitBucket Wiki).
*/

    $("main p").has("img").each(function(){
        var imageAlt = $(this).find("img").attr("alt");
        $(this).append(imageAlt);
        $(this).addClass("paragraph-with-image");
    });

    document.getElementsByClassName("btn-navbar")[0].addEventListener('click', function () {
        /*
            Fixes incorrect hamburger menu scrolling position in responsive mode.
        */
            document.body.scrollTop = 0; // For Safari
            document.documentElement.scrollTop = 0; // For Chrome, Firefox, IE and Opera
        });
});
