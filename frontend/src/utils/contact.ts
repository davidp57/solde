export interface ContactNameLike {
  nom: string | null | undefined
  prenom?: string | null | undefined
}

export function formatContactDisplayName(contact: ContactNameLike): string {
  const firstName = typeof contact.prenom === 'string' ? contact.prenom.trim() : ''
  const lastName =
    typeof contact.nom === 'string' ? contact.nom.trim().toLocaleUpperCase('fr-FR') : ''

  return [firstName, lastName].filter((value) => value.length > 0).join(' ')
}
