#code engine source
vpnupdate.py is the main source.  You can run this locally, I install a virtual python environment first and then:

```
pip install -r requirements.txt
```

Break the vpn connection by inserting the standpy private IP:

```
python vpnupdate.py unfix
```

Do 1/2 the fixup by deleting the route table route

```
python vpnupdate.py fix
```

Do the second 1/2 of the fix by creating a new route to the active member

```
python vpnupdate.py fix
```

If you want to debug in vscode add the following launch configuration:

```
  "configurations": [
    {
      "name": "fix",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/vpnupdate.py",
      "console": "integratedTerminal",
      "args": ["fix"]
    },
    {
      "name": "unfix",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/vpnupdate.py",
      "console": "integratedTerminal",
      "args": ["unfix"]
    }
  ]
```