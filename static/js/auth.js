// Kiểm tra API Key trước khi vào trang
document.addEventListener("DOMContentLoaded", function () {
    let apiKey = localStorage.getItem("api_key");
    if (!apiKey) {
        alert("Bạn chưa đăng nhập!");
        window.location.href = "/login";
    } else {
        console.log( apiKey);
    }
});