document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("register-form");
  const submitBtn = document.getElementById("submit-btn");
  const githubBtn = document.getElementById("github-login-btn");

  form.addEventListener("submit", async function (e) {
    e.preventDefault();

    const username = document.getElementById("username").value;
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const confirmPassword = document.getElementById("confirm-password").value;
    const terms = document.getElementById("terms").checked;

    if (!terms) {
      console.error("Please accept the terms and conditions");
      return;
    }

    if (password !== confirmPassword) {
      console.error("Passwords do not match");
      return;
    }

    if (password.length < 8) {
      console.error("Password must be at least 8 characters long");
      return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = "Creating account...";

    try {
      const response = await fetch("/api/auth/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, email, password }),
      });

      const data = await response.json();

      if (response.ok) {
        document.cookie = `token=${data.token}; path=/; max-age=${60 * 60 * 24 * 7}; SameSite=Lax`;
        window.location.href = "/login/?registered=true";
      } else {
        console.error(data.message || "Registration failed");
        submitBtn.disabled = false;
        submitBtn.textContent = "Register";
      }
    } catch (error) {
      console.error(error);
      submitBtn.disabled = false;
      submitBtn.textContent = "Register";
    }
  });

  githubBtn.addEventListener("click", async function () {
    try {
      const response = await fetch("/api/auth/github");
      const data = await response.json();

      if (data.auth_url) {
        window.location.href = data.auth_url;
      }
    } catch (error) {
      console.error(error);
    }
  });
});
