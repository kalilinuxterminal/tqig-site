import {Link} from 'react-router-dom';
import {Smartphone,ArrowRight,ArrowLeft} from 'lucide-react';
import {WorkspaceShell} from './Workspace';

export default function Phone(){
 return <WorkspaceShell title="On this iPhone" subtitle="Change the location of the phone you’re holding.">
  <main className="portal-main phone-availability">
   <Link className="simple-back" to="/dashboard"><ArrowLeft size={15}/> Back</Link>
   <section className="phone-unavailable-card">
    <div className="simple-mode-icon"><Smartphone size={32}/></div><span className="mode-availability">Not ready yet</span>
    <h2>Phone-only isn’t<br/>ready yet.</h2>
    <p>TQIG currently needs a Windows computer to change an iPhone’s location. A simple phone-only option isn’t available.</p>
    <p className="phone-availability-answer">You can skip the extra apps and setup.</p>
    <div className="phone-current-option"><strong>What works today</strong><p>An iPhone connected to a Windows computer, after its initial setup. The computer must stay on.</p><Link to="/remote" className="button primary">Use with a computer <ArrowRight size={16}/></Link></div>
   </section>
   <details className="simple-details"><summary>Why is an app needed?</summary><p>A website can choose a map pin, but we haven’t established a way for the browser alone to change the iPhone’s system location. Existing on-phone tools use an installed app and a local connection. Their setup and iOS 26.6 behavior still need testing.</p><p>No phone-only success or cellular-only support is claimed.</p></details>
  </main>
 </WorkspaceShell>;
}
