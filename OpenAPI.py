import g4f


g4f.debug.logging = True  # Enable logging
print(g4f.version)  # Check version


if __name__ == "__main__":
    response = g4f.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hello"}],
        stream=True,
    )

    print(response)
                                                                                                                       