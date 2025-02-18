
# tg-bot-quiz

Telegram bot based on a 10-question quiz game. Questions about the Python programming language


## Environment Variables

To run this project, you will need to add the following environment variables to your file

`/.vscode/launch.json'
```
{
    // Use IntelliSense to learn about possible attributes.
    // Hover to view descriptions of existing attributes.
    // For more information, visit: https://go.microsoft.com/fwlink/?linkid=830387
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python Debugger: Current File",
            "type": "debugpy",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal", 
            "env": {
                "API_TOKEN": "123456789qwer"
            }
        }
    ]
} 
```


Replace the value in the "API_TOKEN" field with your TG bot token.
