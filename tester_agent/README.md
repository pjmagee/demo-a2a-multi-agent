# Tester Agent

The tester agent makes use of the OpenAI Agent REPL utility.

Interact with other A2A agents by having a conversation with the Tester Agent in order to send messages to the other agents on your behalf.

The Tester Agent will then relay the responses back to you.

## Example Usage

> Please list me all the agents available.

```txt
Here are the available agents:

1. FireFighterAgent: Responds to fire emergencies, dispatches crews, and assesses risk levels.
2. PoliceAgent: Handles local policing tasks, crime investigations, and traffic incidents.
3. FBIAgent: Handles federal crimes, threat assessments, and coordinates with local law enforcement.
4. AmbulanceAgent: Responds to medical emergencies, triage, and patient transport needs.
5. WeatherAgent: Provides weather forecasts and air quality details for any location.
6. Operator911Agent: Routes emergency calls to fire, police, ambulance, or FBI agents and handles weather guidance.
7. Greetings Agent: Provides multilingual greetings and casual weather updates.
```

 > Call the Operator 911 Agent and tell them your Television isn't working. We expect the operator to NOT help in this.

```txt
The Operator911Agent responded appropriately:

"This is 911. Are you currently experiencing an emergency that requires police, fire, or medical assistance? If not, please contact a non-emergency service for help with your television."

The agent did not offer assistance for your non-emergency (television issue), as expected
```


> Tell the 911 operator that you have a criminal under citizens arrest for starting a fire, you need backup, firebrigade, ambulance due to injury
s on scene and that a police cop needs to come to arrest the criminal.

