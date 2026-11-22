# Professor questions

1. **What does the app do?** It connects material recognition, recycling estimates, local collection and municipal analytics.
2. **What does YOLO do?** It proposes regions where familiar objects appear.
3. **What decides the material?** A trained classification head uses MobileNetV2 features from each crop.
4. **What are the labels?** Plastic, glass, metal and e-waste, plus an internal rejection class.
5. **What is the measured accuracy?** The top label was correct for 400 of 521 target-class test photos. Abstentions count as misses.
6. **How do you measure box quality?** The model card reports a separate street-image benchmark with human-annotated boxes.
7. **What does confidence mean?** It is the classifier’s output score. Calibration was outside the evaluation.
8. **What happens with blur?** Image size and edge variation can trigger a retake state.
9. **Does feedback train the model immediately?** A correction enters a human review queue. Retraining the image model is a separate reproducible operation.
10. **What is stored after a scan?** Predictions, the owner and timestamps. Confirmed records also keep material, weight and the factor snapshot.
11. **How do you estimate value?** Weight in kilograms multiplied by a listed INR/kg rate.
12. **What does the recovery score mean?** It is a representative historical US recycling rate along a 0–100 scale.
13. **How is carbon estimated?** The WARM comparison estimates the difference between landfill and recycling for a representative material.
14. **How is energy estimated?** A representative WARM factor is converted to kWh equivalent and multiplied by weight.
15. **How do you estimate landfill diverted?** The app counts the recorded weight under the assumption that it will be recycled.
16. **Where do locations come from?** OpenStreetMap recycling tags and locally managed records.
17. **How is distance calculated?** The Haversine formula measures the great-circle distance.
18. **What does the forecast learn?** Ridge regression learns seasonal curves from a dated Austin recycling series allocated to simulated wards.
19. **Why do you use a chronological test?** Training on earlier data and evaluating later data matches the direction of forecasting.
20. **What are MAE and RMSE?** MAE averages absolute errors. RMSE gives large errors more weight.
21. **Can Bengaluru use the forecast to schedule trucks?** It is an academic planning scenario. Operational use requires local ground truth and validation.
22. **How is the collection route selected?** The system visits the nearest remaining stop among the highest-volume wards.
23. **How are roles enforced?** FastAPI checks the role associated with the current session before privileged actions.
24. **What does offline mode do?** It serves a cached offline page and prompts the user to reconnect before using online services.
25. **How do you reproduce your results?** Run the setup and test commands, then follow the model card and forecast training guide.
