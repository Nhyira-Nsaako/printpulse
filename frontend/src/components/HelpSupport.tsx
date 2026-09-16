import React from 'react'
import { Mail, MessageSquare } from 'lucide-react'

interface FAQItem {
  q: string
  a: string
}

const CONNECTION_FAQS: FAQItem[] = [
  {
    q: 'Header shows "Offline" instead of "Connected"',
    a: 'The dashboard lost its WebSocket connection to the backend. Refresh the page first. If it stays offline, the backend itself may be down — check status.printpulse (or ask whoever manages the Render deployment) before assuming it\'s your printer.',
  },
  {
    q: 'Live tab shows no data at all',
    a: 'This usually means the ESP32 isn\'t publishing to the MQTT broker, not a dashboard bug. Check: the ESP32 has power and is connected to WiFi, the HiveMQ broker credentials on the device match what\'s configured on the backend, and the device is actually running (check its onboard LED/serial monitor if accessible).',
  },
  {
    q: 'Readings are frozen on an old timestamp',
    a: 'The last MQTT message received is still being shown, but new ones aren\'t arriving. Check the ESP32\'s WiFi signal strength near the printer — intermittent WiFi is the most common cause of gaps like this, not a software fault.',
  },
]

const SENSOR_FAQS: FAQItem[] = [
  {
    q: 'Vibration reading stays near zero even while printing',
    a: 'Check the MPU-6050\'s I2C wiring (SDA/SCL) and that it\'s securely mounted to the printer frame, not loose or vibration-damped by its own mounting. A loose sensor under-reports vibration.',
  },
  {
    q: 'Nozzle temp looks wrong or stuck',
    a: 'This comes from the DS18B20 probe. Confirm its 4.7kΩ pull-up resistor is in place on the 1-Wire line — a missing or wrong-value pull-up is the most common cause of stuck or erratic single-wire temperature readings.',
  },
  {
    q: 'Bed temp looks wrong or missing entirely',
    a: 'Bed temp is read directly from the printer\'s own controller over serial, not a separate probe. If it\'s missing, check the ESP32\'s serial/UART connection to the printer mainboard rather than any sensor wiring.',
  },
  {
    q: 'Fault class seems clearly wrong for what\'s happening',
    a: 'The classifier was trained on a specific feature set — if hardware or wiring changed recently (sensors added/removed, mounting changed), the model may need retraining on fresh data to stay accurate.',
  },
]

function FAQGroup({ title, items }: { title: string; items: FAQItem[] }) {
  return (
    <div className="panel settings-section">
      <div className="settings-heading">{title}</div>
      <div className="settings-grid">
        {items.map((item, i) => (
          <details key={i} className="help-item">
            <summary className="help-item__q">{item.q}</summary>
            <p className="help-item__a">{item.a}</p>
          </details>
        ))}
      </div>
    </div>
  )
}

export function HelpSupport() {
  return (
    <>
      <FAQGroup title="Connection issues" items={CONNECTION_FAQS} />
      <FAQGroup title="Sensor readings" items={SENSOR_FAQS} />

      <div className="panel settings-section">
        <div className="meta-label">Contact</div>
        <div className="settings-heading">Still stuck?</div>
        <div className="settings-grid">
          <div className="setting-row">
            <div className="flex items-center gap-2">
              <Mail size={15} />
              <div>
                <div className="setting-row__title">Email</div>
                <div className="setting-row__desc">support@printpulse.example</div>
              </div>
            </div>
          </div>
          <div className="setting-row">
            <div className="flex items-center gap-2">
              <MessageSquare size={15} />
              <div>
                <div className="setting-row__title">WhatsApp / phone</div>
                <div className="setting-row__desc">+233 XX XXX XXXX</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
