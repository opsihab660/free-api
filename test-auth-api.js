// Test script for the register/login system
// API URL: https://free-api-tvpr.onrender.com

// Generate a random username to avoid conflicts
const generateRandomUsername = () => {
  return `user${Math.floor(Math.random() * 10000)}`;
};

// Test user data
const testUser = {
  username: generateRandomUsername(),
  email: `${generateRandomUsername()}@example.com`,
  password: "Password1234!",
  full_name: "Test User2"
};

console.log("Test user data:", testUser);

// Function to register a new user
async function registerUser() {
  console.log("\n--- Testing User Registration ---");
  try {
    const response = await fetch('https://free-api-tvpr.onrender.com/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(testUser),
    });

    const data = await response.json();
    console.log("Registration Status:", response.status);
    console.log("Registration Response:", data);

    if (response.ok) {
      console.log("✅ Registration successful!");
      return data;
    } else {
      console.log("❌ Registration failed!");
      return null;
    }
  } catch (error) {
    console.error("Error during registration:", error);
    return null;
  }
}

// Function to login a user
async function loginUser() {
  console.log("\n--- Testing User Login ---");
  try {
    const loginData = {
      username: testUser.username,
      password: testUser.password
    };

    const response = await fetch('https://free-api-tvpr.onrender.com/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(loginData),
    });

    const data = await response.json();
    console.log("Login Status:", response.status);
    console.log("Login Response:", data);

    if (response.ok) {
      console.log("✅ Login successful!");
      return data;
    } else {
      console.log("❌ Login failed!");
      return null;
    }
  } catch (error) {
    console.error("Error during login:", error);
    return null;
  }
}

// Function to test API key creation
async function createApiKey(accessToken) {
  console.log("\n--- Testing API Key Creation ---");
  try {
    const keyData = {
      name: "Test API Key"
    };

    const response = await fetch('https://free-api-tvpr.onrender.com/auth/keys', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`
      },
      body: JSON.stringify(keyData),
    });

    const data = await response.json();
    console.log("API Key Creation Status:", response.status);
    console.log("API Key Response:", data);

    if (response.ok) {
      console.log("✅ API Key creation successful!");
      return data;
    } else {
      console.log("❌ API Key creation failed!");
      return null;
    }
  } catch (error) {
    console.error("Error during API key creation:", error);
    return null;
  }
}

// Function to test getting user profile
async function getUserProfile(accessToken) {
  console.log("\n--- Testing User Profile Retrieval ---");
  try {
    const response = await fetch('https://free-api-tvpr.onrender.com/auth/profile', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    });

    const data = await response.json();
    console.log("Profile Retrieval Status:", response.status);
    console.log("Profile Response:", data);

    if (response.ok) {
      console.log("✅ Profile retrieval successful!");
      return data;
    } else {
      console.log("❌ Profile retrieval failed!");
      return null;
    }
  } catch (error) {
    console.error("Error during profile retrieval:", error);
    return null;
  }
}

// Run all tests
async function runTests() {
  console.log("Starting API tests for https://free-api-tvpr.onrender.com");

  // Step 1: Register a new user
  const registrationResult = await registerUser();

  if (!registrationResult) {
    console.log("❌ Tests stopped due to registration failure");
    return;
  }

  // Step 2: Login with the new user
  const loginResult = await loginUser();

  if (!loginResult || !loginResult.access_token) {
    console.log("❌ Tests stopped due to login failure");
    return;
  }

  const accessToken = loginResult.access_token;

  // Step 3: Create an API key
  const apiKeyResult = await createApiKey(accessToken);

  // Step 4: Get user profile
  const profileResult = await getUserProfile(accessToken);

  console.log("\n--- Test Summary ---");
  console.log("Registration:", registrationResult ? "✅ Success" : "❌ Failed");
  console.log("Login:", loginResult ? "✅ Success" : "❌ Failed");
  console.log("API Key Creation:", apiKeyResult ? "✅ Success" : "❌ Failed");
  console.log("Profile Retrieval:", profileResult ? "✅ Success" : "❌ Failed");
}

// Run the tests
runTests();
