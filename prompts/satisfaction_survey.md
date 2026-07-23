# Post-Task Satisfaction Survey

You have just completed a team task. Please reflect on your experience during this task and answer the following questions.

Rate each statement on a scale from 1 to 5.
1 = Strongly Disagree, 2 = Disagree, 3 = Neither Agree nor Disagree, 4 = Agree, 5 = Strongly Agree.

Base your answers ONLY on your experience during the task you just completed.

## Questions

1. The team leader helped the team develop a good approach to the task.
2. The team leader helped the team identify and use each member's strengths.
3. The team leader provided useful feedback during the task.
4. The team leader micromanaged the team's work process.
5. The collaboration within the team worked well.
6. I would work with this team leader again on a future task.

## Response format

You MUST respond with ONLY a valid JSON object in the following format, nothing else:

```json
{"q1": <score>, "q2": <score>, "q3": <score>, "q4": <score>, "q5": <score>, "q6": <score>}
```

Each score must be an integer from 1 to 5. Do not include any explanation or text outside the JSON object.
