function(doc) {
	if (doc['time']) {
	for(var i in doc) {
		if (typeof(doc[i]) == "object") {
			var theTime = new Date(doc['time']*1000);
			var year = theTime.getFullYear();
			var month = theTime.getMonth();
			var daym = theTime.getDate();
			var hours = theTime.getHours();
			var minutes = theTime.getMinutes();
			var seconds = theTime.getSeconds();
			var milliseconds = theTime.getMilliseconds();
			for(var devicename in doc[i]) {
				emit([i,devicename,year,month,daym,hours,minutes,seconds,milliseconds], doc[i][devicename]['value']);
}}}}}
