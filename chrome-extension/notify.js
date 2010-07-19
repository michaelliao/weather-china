function notify_city_change() {
  chrome.extension.connect().postMessage({message: 'city_change'});
}
