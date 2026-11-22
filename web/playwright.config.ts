import {defineConfig} from "@playwright/test";
export default defineConfig({
 testDir:"./e2e",timeout:90000,workers:1,
 use:{baseURL:"http://localhost:3000",launchOptions:{executablePath:process.env.BROWSER_EXECUTABLE},trace:"retain-on-failure"},
 projects:[{name:"mobile-375",use:{viewport:{width:375,height:812},isMobile:true,hasTouch:true}},{name:"mobile-390",use:{viewport:{width:390,height:844},isMobile:true,hasTouch:true}}],
 webServer:{command:"node ../scripts/dev.mjs",url:"http://localhost:3000",timeout:90000,reuseExistingServer:!process.env.CI},
});
