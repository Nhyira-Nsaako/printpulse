                  <td>
                    <span className={`status-text ${e.acknowledged ? 'status-text--ack' : 'status-text--open'}`}>
                      {e.fault_class === 'NORMAL' ? '—' : e.acknowledged ? 'acknowledged' : 'open'}
                    </span>
                  </td>
                  <td>
                    {!e.acknowledged && e.fault_class !== 'NORMAL' && (
                      <div className="ack-group">
                        <input
                          className="input-sm"
                          placeholder="Notes…"
                          value={noteMap[e.id] ?? ''}
                          onChange={ev =>
                            setNoteMap(p => ({ ...p, [e.id]: ev.target.value }))
                          }
                        />
                        <button
                          className="ack-link"
                          onClick={() => {
                            onAcknowledge(e.id, noteMap[e.id])
                            setNoteMap(p => {
                              const n = { ...p }
                              delete n[e.id]
                              return n
                            })
                          }}
                        >
                          Acknowledge
                        </button>
                      </div>
                    )}
                    {e.notes && <div className="ack-note">{e.notes}</div>}
                  </td>
