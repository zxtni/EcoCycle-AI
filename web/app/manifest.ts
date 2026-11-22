import type { MetadataRoute } from "next";
export default function manifest(): MetadataRoute.Manifest {
 return { name:"EcoCycle AI", short_name:"EcoCycle", start_url:"/", scope:"/", display:"standalone", background_color:"#f5f7f5", theme_color:"#103f36", icons:[{src:"/icon-192.png",sizes:"192x192",type:"image/png"},{src:"/icon-512.png",sizes:"512x512",type:"image/png",purpose:"any"}] };
}
