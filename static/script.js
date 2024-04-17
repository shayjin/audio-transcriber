document.getElementById('mp3_file').addEventListener('change', function() {
    const selectedFile = this.files[0];
    document.getElementById('selectedFile').innerText = `Selected File: ${selectedFile.name}`;
});

var children = document.getElementById("mp3").children;

for (var child of children) {
    (function(x) {
        child.addEventListener('click', function() {
            document.getElementById('selectedFile').innerHTML = "Selected: " + x;
            var dummyData = "test.mp3"; 
            var blob = new Blob([dummyData], { type: 'audio/mpeg' });
            var dummyFile = new File([blob], 'test.mp3', { type: 'audio/mpeg' });
            document.getElementById('mp3_file').files = [dummyFile];
        });
    })(child.innerHTML);
}

function downloadTextFile(result) {
    var textContent = result.replaceAll("ㄱ", "'");
    var blob = new Blob([textContent], { type: 'text/plain' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = 'result.txt';
    a.click();
    URL.revokeObjectURL(url);
}

function showLoading() {
    document.getElementById('upload').style.display = 'none';
    document.getElementById('loading').style.display = 'block';
    startTimer();
}

var startTime;

function startTimer() {
    startTime = new Date().getTime();
    updateTimer();
    document.getElementById('timerDisplay').style.display = 'block';
}

function updateTimer() {
    var currentTime = new Date().getTime();
    var elapsedTime = currentTime - startTime;
    var hours = Math.floor(elapsedTime / (1000 * 60 * 60));
    var minutes = Math.floor((elapsedTime % (1000 * 60 * 60)) / (1000 * 60));
    var seconds = Math.floor((elapsedTime % (1000 * 60)) / 1000);
    var timerDisplay = document.getElementById('timerDisplay');
    timerDisplay.textContent = 'Time Spent: ' + formatTime(hours) + ':' + formatTime(minutes) + ':' + formatTime(seconds);
    setTimeout(updateTimer, 1000);
}

function formatTime(time) {
    return (time < 10 ? '0' : '') + time;
}

function attachFileFromDrive(fileInfo) {
    console.log(fileInfo);
    var fileInput = document.getElementById('mp3_file');
    var fileBlob = new Blob([''], { type: 'audio/mp3' });
    fileBlob.name = fileInfo.name;
    var file = new File([fileBlob], fileBlob.name, { 
        type: 'audio/mp3', 
        lastModified: Date.now(), 
    });
    var fileList = new DataTransfer();
    fileList.items.add(file);
    fileInput.files = fileList.files;
    document.getElementById("id").setAttribute("value", fileInfo.id);
    document.getElementById('selectedFile').innerText = "Selected File: " + fileInfo.name;
    console.log(fileInput.files);
}