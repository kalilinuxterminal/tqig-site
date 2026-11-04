import {lazy,Suspense,useEffect,useState} from 'react';
import {Link} from 'react-router-dom';
import {motion,useReducedMotion} from 'motion/react';
import {ArrowRight,ArrowUp,ArrowUpRight,Bookmark,Cable,Car,Check,ChevronDown,Footprints,Globe2,MapPin,MousePointer2,RotateCcw,ShieldCheck,Smartphone,TrendingUp} from 'lucide-react';
import {Navbar} from '../components/Navbar';
import {Logo} from '../components/Logo';
import {places} from '../services/types';
const WorldMap=lazy(()=>import('../components/WorldMap'));
const faqs=[
 ['What do I need to get started?','A Windows computer and your iPhone. Connect the iPhone, unlock it, approve Trust, and complete the Developer Mode and Apple device support steps in TQIG. Keep the computer running and the phone connected during simulation.'],
 ['Can I do this with only my iPhone?','Phone-only mode is not ready. The available workflow needs a Windows computer. Experimental Wi-Fi still needs that computer; it does not turn TQIG into a phone-only service.'],
 ['What happens when I choose a place?','Choosing a map pin only changes your selection. Press Set Location to send it to the connected iPhone, then check the result in Apple Maps.'],
 ['How do I go back to my real location?','Use Stop & Restore while the iPhone is connected, then confirm that its apps have returned to your real location. Reconnect the phone if its connection was interrupted.'],
 ['Does it work with my apps?','Foreground set and restore were observed in Apple Maps, Snapchat, Life360 and Find My on one test iPhone running iOS 26.6. Other versions, background updates and driving reports still need independent validation.'],
 ['Can I look around before signing in?','Yes. The map on this page is an interactive website preview, and the public video shows the workspace. Neither applies a location to your iPhone. Accounts require an invitation to sign up.'],
];
const experiences=[
 {icon:MapPin,kicker:'A CHANGE OF PLACE',title:'Somewhere different.',text:'Find a city, an address, or that exact spot by the lake. Drop a pin, save it, and come back whenever you like.',link:'Explore the map',to:'/app',kind:'place'},
 {icon:Footprints,kicker:'AT YOUR OWN PACE',title:'Take the scenic route.',text:'Plan a walk with your own pace, time at the destination, and a return to the starting point.',link:'Plan a walk',to:'/app/walk',kind:'walk'},
 {icon:Car,kicker:'BEYOND A SINGLE PIN',title:'Make a journey of it.',text:'Follow real roads, choose a driving pace, stay for a while, and plan the way back.',link:'Plan a drive',to:'/app/drive',kind:'drive'},
];

export default function Landing(){
 const reduced=useReducedMotion(),[showTop,setShowTop]=useState(false);
 const reveal={initial:reduced?false:{opacity:0,y:20},whileInView:{opacity:1,y:0},viewport:{once:true,margin:'-35px'},transition:{duration:.5}};
 useEffect(()=>{const update=()=>setShowTop(window.scrollY>650);update();window.addEventListener('scroll',update,{passive:true});return()=>window.removeEventListener('scroll',update);},[]);
 return <div className="landing index-v2"><Navbar/>
  <main id="main-content" tabIndex={-1}>
   <section className="index-hero section-width">
    <motion.div className="index-hero-copy" initial={reduced?false:{opacity:0,y:20}} animate={{opacity:1,y:0}} transition={{duration:.6}}>
     <span className="index-kicker"><span/> A LITTLE CHANGE OF SCENERY</span>
     <h1>Your location.<br/><span>Your choice.</span></h1>
     <p>Pick a place. Plan a walk or a drive.<br/>Choose what comes next for your connected iPhone.</p>
     <div className="index-hero-actions"><Link to="/dashboard" className="button primary">Open your workspace <ArrowUpRight size={18}/></Link><Link to="/preview" className="index-preview-link">Watch the preview <ArrowRight size={16}/></Link></div>
     <div className="index-requirement"><Cable size={16}/><span>Windows computer required <i>·</i> Tested on iOS 26.6</span></div>
    </motion.div>
    <motion.div className="index-map-preview" initial={reduced?false:{opacity:0,y:20}} animate={{opacity:1,y:0}} transition={{duration:.7,delay:.1}}>
     <div className="index-preview-top"><span><Globe2 size={15}/> THE WORLD IS OPEN</span><small>Interactive preview</small></div>
     <div className="index-map-frame"><Suspense fallback={<div className="map-loading">Opening Clermont…</div>}><WorldMap hero selected={places[0]} reducedMotion={!!reduced}/></Suspense></div>
     <div className="index-preview-location"><span className="index-location-icon"><MapPin size={21}/></span><div><small>A PLACE TO START</small><strong>Clermont, Florida</strong><span>28.5550° N · 81.7662° W</span></div><Link to="/app" aria-label="Explore Clermont on the map"><ArrowUpRight size={21}/></Link></div>
    </motion.div>
   </section>
   <div className="index-benefits section-width"><span><MapPin size={16}/> One place or a whole journey</span><span><Bookmark size={16}/> Keep your favorite places</span><span><RotateCcw size={16}/> Stop & Restore when you’re ready</span></div>

   <section className="index-experiences section-width" id="features">
    <motion.div {...reveal} className="index-section-heading"><div><span className="index-kicker">YOUR NEXT POSSIBILITY</span><h2>More than a pin<br/><span>on a map.</span></h2></div><p>A simple workspace for places, walks, and drives.<br/>Start with the kind of change you have in mind.</p></motion.div>
    <div className="index-experience-grid">{experiences.map((item,i)=><motion.article {...reveal} transition={{duration:.5,delay:i*.06}} className={'index-experience '+item.kind} key={item.kind}><div className="index-feature-icon"><item.icon size={25}/></div><span className="index-card-kicker">{item.kicker}</span><h3>{item.title}</h3><p>{item.text}</p><div className="index-mini-route" aria-hidden="true"><svg viewBox="0 0 300 90"><path d={i===0?'M18 65H85Q102 65 102 48V20H280':i===1?'M18 65C70 65 54 15 110 25S180 78 215 40S255 25 280 20':'M18 65H80V25H160V65H230V20H280'} fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/><circle cx="18" cy="65" r="4" fill="currentColor"/><circle cx="280" cy="20" r="6" fill="currentColor"/></svg></div><Link className="index-card-link" to={item.to}>{item.link} <ArrowUpRight size={16}/></Link></motion.article>)}</div>
   </section>

   <section className="index-how section-width" id="how-it-works">
    <motion.div {...reveal} className="index-section-heading"><div><span className="index-kicker">A CLEAR WAY TO BEGIN</span><h2>Connect. Choose.<br/><span>Make your move.</span></h2></div><Link className="index-inline-link" to="/support">Setup & connection help <ArrowUpRight size={15}/></Link></motion.div>
    <div className="index-steps">{[{n:'01',icon:Cable,title:'Connect your iPhone.',text:'Use your Windows computer and complete the guided connection steps. Keep the phone connected while you use TQIG.'},{n:'02',icon:MousePointer2,title:'Find your place.',text:'Search an address, tap the map, or choose a saved favorite. You can also plan a walk or drive.'},{n:'03',icon:Check,title:'Set it. Check it. Restore.',text:'Apply your selection, verify it on the iPhone, and use Stop & Restore when you’re finished.'}].map(step=><motion.article {...reveal} key={step.n}><div><span>{step.n}</span><step.icon size={22}/></div><h3>{step.title}</h3><p>{step.text}</p></motion.article>)}</div>
   </section>

   <section className="index-connection section-width" id="compatibility">
    <motion.div {...reveal} className="index-connection-copy"><span className="index-kicker">YOUR SETUP, EXPLAINED</span><h2>Know what’s<br/><span>connected.</span></h2><p>TQIG is a website with Windows connection software. Your Apple pairing records stay on your computer. You don’t need to give TQIG your Apple ID password.</p><Link className="index-inline-link" to="/support#compatibility">Read the compatibility details <ArrowUpRight size={15}/></Link></motion.div>
    <div className="index-availability"><article><span className="index-availability-icon"><Cable size={22}/></span><div><small>AVAILABLE WORKFLOW</small><h3>Windows + connected iPhone</h3><p>USB location set and restore were tested on iOS 26.6. Foreground checks included Apple Maps, Snapchat, Life360 and Find My on one phone.</p><span className="index-tested"><Check size={12}/> Test results, not a universal guarantee</span></div></article><article><span className="index-availability-icon"><Smartphone size={22}/></span><div><small>STILL IN DEVELOPMENT</small><h3>Only the phone you’re holding</h3><p>A simple phone-only mode is not ready yet. Experimental Wi-Fi still requires a Windows computer.</p><Link to="/phone">View availability <ArrowUpRight size={13}/></Link></div></article></div>
   </section>

   <section className="index-faq section-width" id="questions"><div><span className="index-kicker">BEFORE YOU GET STARTED</span><h2>Good questions.<br/><span>Clear answers.</span></h2><p>A few things worth knowing before your first change of place.</p><Link className="index-inline-link" to="/support">More help <ArrowUpRight size={15}/></Link></div><div className="index-faq-list">{faqs.map(([q,a])=><details key={q}><summary>{q}<ChevronDown size={17}/></summary><p>{a}</p></details>)}</div></section>
   <section className="index-extra section-width"><TrendingUp size={24}/><div><small>ALSO IN YOUR WORKSPACE</small><h3>A little progress, worth keeping.</h3><p>Log your Snapscore manually and follow your progress toward a goal.</p></div><Link to="/snapscore">Open tracker <ArrowUpRight size={16}/></Link></section>
   <section className="index-final section-width"><span className="index-kicker">A DIFFERENT PERSPECTIVE STARTS HERE</span><h2>Where to next?</h2><Link to="/dashboard" className="button primary">Open your workspace <ArrowUpRight size={18}/></Link><p>Invite-only accounts. Public preview. Windows required.</p></section>
  </main>
  <footer className="site-footer section-width"><Logo/><p>Explore thoughtfully. Stay in control.</p><nav aria-label="Footer"><Link to="/privacy">Privacy</Link><Link to="/terms">Preview terms</Link><Link to="/support">Support</Link></nav><small>© {new Date().getFullYear()} TQIG · tqig.space</small></footer>
  {showTop&&<button type="button" className="back-to-top" aria-label="Back to top" onClick={()=>window.scrollTo({top:0,behavior:reduced?'auto':'smooth'})}><ArrowUp size={18}/></button>}
 </div>;
}
