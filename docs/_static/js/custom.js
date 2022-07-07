window.addEventListener('load', function () {
  extractImgDescriptions();
  hamburgerScrollingFix();
  hideTerminalSig();
});

function extractImgDescriptions() {
  /*
  The jQuery script below extracts image descriptions that are "hidden" into
  the alt attribute by the myst_parser Sphinx extension and makes them visible
  by appending them to the parent paragraphs (just like they appear in the
  BitBucket Wiki).
  */

  $("main p").has("img").each(function () {
    var imageAlt = $(this).find("img").attr("alt");
    $(this).append(imageAlt);
    $(this).addClass("paragraph-with-image");
  });
}

function hamburgerScrollingFix() {
  // Fixes incorrect hamburger menu scrolling position in responsive mode.

  document.getElementsByClassName("btn-navbar")[0].addEventListener('click', function () {
    document.body.scrollTop = 0; // For Safari
    document.documentElement.scrollTop = 0; // For Chrome, Firefox, IE and Opera
  });
}

function hideTerminalSig() {
  /*
  Appends .sig class to hide the function's terminal signatures.
   */
  var commandH1Content = jQuery.trim($("h1")[1].innerHTML);

  $("dd p").first("code span").each(function () {
    var spanElement = $(this).find("span:first");
    var spanContent = jQuery.trim(spanElement.text().slice(0, commandH1Content.length));
    if (spanContent == commandH1Content) {
      $(this).addClass("sig");

      $(this).next().has("code span").each(function () {
        $(this).addClass("sig");
      });
    }
  });
}