from openai import OpenAI

client = OpenAI(
    api_key="ddc-temp-free-e3b73cd814cc4f3ea79b5d4437912663",
    base_url="https://api.devsdocode.com/v1"
)

completion = client.chat.completions.create(
      model="provider-4/o3-mini",
      messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
      ]
    )

print(completion)












from openai import OpenAI

client = OpenAI(
    api_key="user_key_VujKhs324ykqW2SlLG0Klrig",
    base_url="https://free-api-tvpr.onrender.com/v1/api"
)

completion = client.chat.completions.create(
      model="gpt-4.1",
      messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
      ]
    )

print(completion)
