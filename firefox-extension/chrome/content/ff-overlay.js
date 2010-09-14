weatherchina.onFirefoxLoad = function(event) {
  document.getElementById("contentAreaContextMenu")
          .addEventListener("popupshowing", function (e){ weatherchina.showFirefoxContextMenu(e); }, false);
};

weatherchina.showFirefoxContextMenu = function(event) {
  // show or hide the menuitem based on what the context menu is on
  document.getElementById("context-weatherchina").hidden = gContextMenu.onImage;
};

window.addEventListener("load", weatherchina.onFirefoxLoad, false);
