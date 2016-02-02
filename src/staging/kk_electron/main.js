var app = require('app');
app.commandLine.appendSwitch('enable-smooth-scrolling', true);
var BrowserWindow = require('browser-window');
var mainWindow = null;

var j = require('jscloak');
var sprintf = j.utils.sprintf;

app.on('ready', function() {
   // Create the browser window.
   mainWindow = new BrowserWindow({
	  'width' : 802,
	  'height' : 375,
     'center' : true,
	  'frame' : false,
	  'resizable ' : false,
	  'transparent' : false,
	  'overlay-scrollbars' : false,
	  'title-bar-style': 'hidden'
   });

	var wc = mainWindow.webContents;

	var debug = false;
	for (x in process.argv) {
		switch (process.argv[x]) {
		case '--debug':
			debug = true;
			break;
		default:
			break;
		}
	}

	//var cmd = utils.sprintf('init_updater_api(%s);', debug);
	//wc.executeJavaScript(cmd);

   // and load the index.html of the app.
	var url = sprintf('file://%s/index.html', __dirname);
   mainWindow.loadURL(url);


   // Open the DevTools.
   if (debug)
      mainWindow.openDevTools();

   // Emitted when the window is closed.
   mainWindow.on('closed', function() {
      // Dereference the window object, usually you would store windows
      // in an array if your app supports multi windows, this is the time
      // when you should delete the corresponding element.
      //wc = null;
      mainWindow = null;
   });
});

app.on('window-all-closed', function() {
   if (process.platform != 'darwin') {
      app.quit();
   }
});


