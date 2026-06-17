import { ShieldAlert } from "lucide-react";

export function EthicsBanner() {
  return (
    <section className="ethics-banner" aria-label="Ethics notice">
      <ShieldAlert size={18} />
      <p>
        GAIA-1 is a neuron-ready planetary simulation. This MVP runs on the Cortical Labs CL SDK
        Simulator and does not use real neurons. Planetary signals are encoded into stimulation
        intents, simulated neural spikes are decoded into actions, and a digital Earth evolves in
        real time. The architecture is designed for future deployment to biological neural networks
        through CL1/Cortical Cloud. Simulator mode: no real neurons are connected.
      </p>
    </section>
  );
}
