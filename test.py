from openai import OpenAI

client = OpenAI(
    api_key="user_key_kimH7IYsIBVQZ5ZVGHQtkTPV",
    base_url="https://free-api-tvpr.onrender.com/v1/api"
)

completion = client.chat.completions.create(
      model="gpt-4o",
      messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
      ]
    )

print(completion)
