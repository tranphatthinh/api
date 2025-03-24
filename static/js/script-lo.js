document.getElementById("loginForm").addEventListener("submit", function (event) {
    event.preventDefault();

    let email = document.getElementById("email").value;
    let password = document.getElementById("password").value;

    fetch("http://127.0.0.1:5000/login", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ email: email, password: password })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error); // Hiển thị lỗi nếu có
        } else {
            alert(data.message); // Hiển thị thông báo đăng nhập thành công
            localStorage.setItem("api_key", data.api_key); // Lưu API Key vào localStorage
            window.location.href = "/grammar-check"; // Chuyển hướng
        }
    })
    .catch(error => console.error("Lỗi:", error));
});