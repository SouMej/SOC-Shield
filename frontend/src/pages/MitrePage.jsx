import { motion } from 'framer-motion';
import { Shield } from 'lucide-react';
import MitreHeatmap from '../components/dashboard/MitreHeatmap';

export default function MitrePage() {
  return (
    <div>
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: 4 }}>
          <Shield size={24} style={{ verticalAlign: 'middle', marginRight: 10 }} />
          MITRE ATT&CK
        </h1>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          Technique coverage map and detected attack patterns
        </p>
      </motion.div>
      <MitreHeatmap />
    </div>
  );
}
