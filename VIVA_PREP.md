# EcoCycle AI viva preparation

## 30-second introduction

“EcoCycle AI is a recycling assistance platform. A citizen uploads a photo, reviews the suggested object and material, confirms the weight, and saves an estimated recycling impact. The app also helps users find collection centers. A separate municipality dashboard reports recorded activity and demonstrates weekly collection forecasting. The app runs on a VPS, and the scan uses trained models that run on the CPU.”

## Basics and project defense

1. **What problem are you solving?** People may know an item can be recycled but may be unsure of its material, disposal options, or value. EcoCycle puts these steps in one workflow.
2. **What are your objectives?** Identify common items and materials, guide the user through recycling, track estimates and give municipality staff a reporting interface.
3. **Who uses it?** Citizens scan items and record recycling. Municipal staff view summaries, reports and corrections.
4. **What is a circular economy?** It keeps products and materials in use through reuse, repair and recycling, reducing the need for new raw materials.
5. **What is your contribution?** The project integrates the scan pipeline, correction flow, estimates, collection locator and municipality tools into a deployed application. Explain your personal contribution using only the work you actually did.
6. **Why use AI here?** A photo can help users identify unfamiliar items. The user still reviews the suggestion and confirms the weight and material.
7. **What is the scope?** The material categories are plastic, glass, metal and electronics for recycling. V4 also names selected objects such as bottles, laptops, sunglasses and watches.
8. **What is a key limitation?** A photo gives visual clues. Mixed materials, shiny objects, clutter and very small items are difficult, and disposal intent requires user confirmation.

## Tech stack, database and security

9. **Which technologies are used?** Next.js, React and TypeScript for the frontend. FastAPI and Python for the API. SQLAlchemy and Alembic for data access and migrations. SQLite locally, PostgreSQL on Supabase in production. ONNX Runtime for inference. Docker and aaPanel for the VPS deployment.
10. **Why Next.js?** It organizes routes, serves the frontend and forwards same-origin API requests to FastAPI.
11. **Why FastAPI?** It connects directly to the Python model code and provides input validation and interactive OpenAPI documentation.
12. **Why two databases?** SQLite gives an easy laptop demo with one local file. PostgreSQL is the production database for concurrent users.
13. **What are the key tables?** Users, login sessions, scans, feedback, collection centers and the admin audit log. A scan belongs to a user and can have a correction.
14. **What is a migration?** A versioned change to the database schema. Alembic applies the same schema change to the local or production database.
15. **How does login work?** Users register with email and password. Passwords are salted and hashed with scrypt. A successful login issues a random session token in an HTTP-only cookie. The server stores a hash of the token.
16. **Can a citizen call an admin API?** The server checks the role on privileged endpoints. A logged-in citizen receives HTTP 403 when attempting those operations.
17. **What happens when a photo is uploaded?** The API checks session, image format and size, decodes the image, corrects orientation, and reduces the size before inference.
18. **What runs where?** Docker runs Next.js and FastAPI on the VPS. aaPanel’s Nginx serves HTTPS and proxies to Next.js. Next.js forwards API requests to the backend on the Docker network.
19. **What needs internet?** Installation, live map tiles and live OpenStreetMap listings. After setup, the local scanner, database, estimates and report exports can run without internet.
20. **How did you test it?** API and calculator tests cover validation and access control. Playwright checks sign-in, real photo scan, impact save and locator navigation at 375 and 390 px. There were also live deployment checks.

## AI models and evaluation

21. **Which models are used?** A COCO-trained YOLOv8n proposes material regions. A MobileNetV2-based head predicts material from crops. V4 adds a separately fine-tuned YOLOv8n Open Images model to detect selected object names and boxes.
22. **Why use two result types?** Object labels answer what the item looks like. Material labels estimate what it is made of. A bottle can be plastic or glass.
23. **What is transfer learning?** Starting from a model trained on a larger dataset and adapting it to a new task. The material model freezes MobileNetV2 features and trains a class-balanced logistic regression head.
24. **Did you train everything from scratch?** We used pretrained checkpoints. The material head was fitted on waste photographs, and the V4 object detector was fine-tuned for four epochs with its first ten modules frozen.
25. **Which datasets did you use?** TrashNet and the E Waste Image Dataset for material training. Open Images for the object detector. A small TACO street-photo sample tested generalization separately.
26. **How much training data did you use?** The material head used 4,159 photos and 7,061 views after including crops. V4 fine-tuned on 95 images, used 25 for checkpoint selection, and evaluated on 60 held-out annotations across five categories.
27. **What is a bounding box?** A rectangle around the object. The API represents its corners using normalized coordinates between 0 and 1.
28. **What is IoU?** Intersection over Union is overlap area divided by union area. The object benchmark requires at least 0.50 IoU and the correct object name.
29. **What is the latest object detection score?** Detailed mode matched 35 of 48 held-out annotations across the four app-visible categories, or 72.9%. Standard mode matched 31 of 48. These are correct name-and-box matches on that subset.
30. **What is the material accuracy?** The separate v3 standard material benchmark measured 399 of 521 correct, or 76.6%, with abstentions counted as misses. The v4 object score measures a different task. A separate v4 end-to-end material result is undocumented.
31. **What does 99%+ confidence mean?** The model assigned a high score to this prediction. Confidence calibration was outside the evaluation, so use the user-confirmation step.
32. **What are precision and recall?** Precision asks how many model detections are correct. Recall asks how many labeled objects the model successfully found.
33. **Why are field photos harder?** Lighting, clutter, size, occlusion and camera angles differ from many training photos. This difference in data distribution is called domain shift.
34. **How does detailed search work?** It runs on overlapping crops, maps the coordinates back to the original image and filters duplicate boxes. It can recover small objects at higher inference cost.
35. **Can it identify a smartwatch?** The detector has a general Watch class. It may recognize a smartwatch as a watch, but the benchmark does not validate a separate smartwatch class.
36. **Why did my laptop appear as electronics?** The scan can suggest that it is an electronic object. It becomes a saved e-waste record only when the user confirms disposal for recycling.
37. **What is ONNX?** A portable model format. ONNX Runtime loads the exported network to run inference on the CPU, so the deployment does not need the training framework.
38. **What happens if a prediction is wrong?** The user can choose the correct material and submit feedback. Admins can review corrections. These records do not automatically retrain the detector.
39. **How would you improve it further?** Collect diverse annotated phone photographs. Keep shots of the same physical item in the same split. Compare the new model on untouched whole scenes, measuring recall, false positives and runtime.

## Calculations, maps and forecasting

40. **How do you calculate recycling value?** Multiply the confirmed weight in kg by the reference material price in INR per kg.
41. **How do you estimate carbon and energy savings?** Multiply weight by the versioned material-specific factors. The app stores the factor version with the record.
42. **How is landfill diversion measured?** The app uses the weight the user records for recycling as an estimate. It cannot observe what physically happens to the item.
43. **How does the locator work?** The API queries OpenStreetMap via Overpass and Leaflet renders the results. The app filters by distance and available material tags. Local sample centers are synthetic.
44. **Where does the forecast data come from?** The real source is Austin’s collection history. The project aggregates it by week and generates illustrative allocations to six Bengaluru wards.
45. **What forecast model did you choose?** Ridge regression uses a ward baseline and annual seasonal terms. It is small, explainable and quick to retrain.
46. **Why split forecasting data chronologically?** Training uses earlier weeks and evaluation uses later weeks. This reflects how the model would be used to predict future observations.
47. **What did the forecast score?** MAE was 1,564.57 kg and RMSE was 2,144.14 kg per simulated ward-week on 312 held-out rows. Real Bengaluru forecasting accuracy remains unmeasured.
48. **What is the difference between MAE and RMSE?** MAE averages absolute errors. RMSE squares errors first and therefore gives large misses more weight.
49. **Can a municipality directly dispatch trucks from this app?** It can demonstrate the planning workflow. Actual dispatch needs local collection weights, verified stops, road-network travel times and route constraints.
50. **What would you do if the venue internet fails?** Launch the extracted laptop package with RUN-DEMO.cmd after installing dependencies beforehand. Use the bundled plastic photo, local demo accounts and report exports.

## Quick revision

- Memorize the flow in order. Upload photo, review object and material, confirm weight, save impact, find a collection center.
- Keep the three numbers distinct. **35/48** v4 object localization, **399/521** v3 material classification, **1,564.57 kg** forecast MAE on simulated ward-weeks.
- Show the working plastic photo first. Then show sunglasses to explain the difference between object and material results.
- If asked about tools or collaboration, describe your actual role and how you verified the result.

Evidence: [Model card](MODEL_CARD.md), [detector training](docs/detector-pilot.md), [forecast method](docs/forecast-method.md), [architecture](ARCHITECTURE.md), [laptop demo](LOCAL_DEMO.md).
