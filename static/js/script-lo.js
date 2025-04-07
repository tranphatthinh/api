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
        if (data.access_token) {
            console.log("API Key nhận được:", data.access_token);
            
            // 👉 Lưu token vào localStorage để dùng trong request tiếp theo
            localStorage.setItem("access_token", data.access_token);

            // 👉 Chuyển hướng sang trang kiểm tra ngữ pháp
            window.location.href = "/check-grammar";
        } else {
            alert("Đăng nhập thất bại! Vui lòng kiểm tra lại email và mật khẩu.");
        }
    })
    .catch(error => console.error("Lỗi:", error));
});