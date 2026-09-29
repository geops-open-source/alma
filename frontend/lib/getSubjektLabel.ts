interface Subjekt {
  name?: string;
  subjId: string;
  taetigkeit?: string;
  vorname?: string;
}

export default function getSubjektLabel(subjekt: Subjekt): string {
  let label = `(ID: ${subjekt.subjId})`;
  const name = [subjekt.vorname, subjekt.name].filter(Boolean).join(" ");
  if (name && subjekt.taetigkeit) {
    label = `${name}, ${subjekt.taetigkeit}`;
  } else if (name) {
    label = name;
  } else if (subjekt.taetigkeit) {
    label = subjekt.taetigkeit;
  }
  return label;
}
