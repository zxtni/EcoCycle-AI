import {expect,test} from "@playwright/test";
import path from "node:path";
test.use({permissions:["geolocation"],geolocation:{latitude:19.076,longitude:72.8777}});
test("citizen signs in, scans a photo, saves impact and locates centers",async({page,request},testInfo)=>{
 const email="student-"+Date.now()+"-"+testInfo.project.name+"@example.org";
 const password="A local test passphrase";
 const registration=await request.post("/api/auth/register",{data:{email,password,name:"Mobile Student"}});
 expect(registration.status()).toBe(201);
 await page.goto("/scan");
 await page.getByLabel("Email").fill(email);
 await page.getByLabel("Password",{exact:true}).fill(password);
 await page.getByRole("button",{name:"Sign in",exact:true}).last().click();
 const progress=page.getByRole("list",{name:"Scan progress"}).locator('[aria-current="step"]');
 await expect(progress).toContainText("Photo");
 await page.getByLabel("Upload photo").setInputFiles(path.resolve("../backend/vision_assets/demo-plastic.jpg"));
 await page.getByRole("button",{name:"Analyze photo"}).click();
 await expect(page.getByRole("heading",{name:"Detected materials"})).toBeVisible();
 await expect(progress).toContainText("Review");
 await expect(page.getByText(/plastic · .*confidence/)).toBeVisible();
 await page.getByLabel("Weight (kg)").fill("0.125");
 await page.getByRole("button",{name:"Calculate estimate"}).click();
 await page.getByRole("button",{name:"Save to my impact"}).click();
 await expect(page.getByText("Saved to")).toBeVisible();
 await expect(progress).toContainText("Save");
 await expect(page.getByRole("button",{name:"Analyze photo"})).toBeDisabled();
 const nearby=pendingNearbyRequest();
 await page.getByRole("navigation").last().getByRole("link",{name:"Center locator"}).click();
 await nearby;
 await expect(page.getByText("Searching near your location.")).toBeVisible();
 await expect(page.getByRole("heading",{name:"Center locator"})).toBeVisible();
 await expect(page.getByRole("heading",{name:/nearby results?/})).toBeVisible({timeout:45000});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(testInfo.project.use.viewport!.width);
 function pendingNearbyRequest(){
   return page.waitForRequest(request=>{
     const url=new URL(request.url());
     return url.pathname==="/api/centers"&&url.searchParams.get("lat")==="19.076"&&url.searchParams.get("lon")==="72.8777";
   });
 }
});
