importScripts('config.js');

// Klik na ikonu rozšíření otevře Projekci
chrome.action.onClicked.addListener(() => chrome.tabs.create({ url: PROJEKCE_URL }));
