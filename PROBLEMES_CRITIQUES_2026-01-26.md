# 🚨 Problèmes Critiques AI Orchestrator

**Date**: 2026-01-26
**Status**: IDENTIFIÉS - CORRECTIONS EN COURS

---

## 📋 Résumé des 3 Problèmes

1. ❌ **Hallucinations** : L'AI invente encore des chemins qui n'existent pas
2. ⚠️ **READMEs erronés** : L'AI croit aveuglément ce qui est écrit dans les READMEs
3. ❌ **Feedback cassé** : Le système de feedback ne fonctionne pas ("Token manquant")

---

## 🔍 Problème 1 : Hallucinations (EN COURS)

### Symptômes

Quand vous demandez : "Liste les fichiers dans /home/lalpha/projets/ai-tools"

**L'AI répond** :
```
/home/lalpha/projets/ai-tools
/home/lalpha/projets/ai-tools/src    ← N'EXISTE PAS !
/home/lalpha/projets/ai-tools/tests
```

**Test utilisateur** :
```bash
$ ls /home/lalpha/projets/ai-tools/src
ls: cannot access '/home/lalpha/projets/ai-tools/src': No such file or directory
```

### Cause

Le fix anti-hallucination a été appliqué MAIS le backend n'avait pas rechargé le code Python.

### ✅ Correction Appliquée

1. ✅ Fix dans `engine.py` (section GESTION DES ERREURS)
2. ✅ Backend redémarré (PID: 2643713)
3. ✅ Health check OK

### 🎯 Action Requise

**VOUS devez re-tester maintenant** :

1. Allez sur : https://ai.4lb.ca
2. Nouvelle conversation
3. Demandez : "Liste tous les fichiers dans /home/projets"
4. Vérifiez :
   - ✅ Message d'erreur clair "Le répertoire n'existe pas"
   - ❌ Pas de liste de fichiers inventés

**Si ça marche** : ✅ Problème résolu
**Si ça ne marche PAS** : Envoyez screenshot

---

## ⚠️ Problème 2 : READMEs Erronés

### Symptômes

Votre README.md dit :
```markdown
Ce projet utilise :
- numpy>=1.21.0
- pandas>=1.3.0
- scikit-learn>=0.24.0
```

**L'AI répond** :
```
Ce projet utilise numpy, pandas, scikit-learn, flask...
```

**Mais le vrai requirements.txt** :
```
requests==2.28.0
beautifulsoup4==4.11.1
# Pas de numpy !
```

### Cause

L'AI lit le README et le traite comme source de vérité absolue, sans vérifier les fichiers de configuration réels.

### ✅ Solution Proposée

Ajouter au prompt système :

```python
## VÉRIFICATION DES SOURCES

Quand tu analyses un projet :
1. NE JAMAIS faire confiance aveuglément aux READMEs
2. TOUJOURS vérifier les fichiers réels (requirements.txt, package.json)
3. Si différence : signaler et privilégier les fichiers de config

Exemple BON :
"Le README indique numpy et pandas, mais requirements.txt contient seulement requests et beautifulsoup4.
Le README est probablement obsolète."
```

### 🎯 Voulez-Vous Que J'Applique Ce Fix ?

**Option A** : Oui, applique-le maintenant (5 min)
**Option B** : Non, pas urgent

**Document détaillé** : `PROBLEME_README_ERRONE.md`

---

## ❌ Problème 3 : Système de Feedback Cassé

### Symptômes

Dans la console du navigateur :
```
❌ Erreur feedback positif: Token manquant
❌ Erreur feedback positif: Error: Token manquant
```

Quand vous cliquez sur 👍 ou 👎, rien n'est enregistré.

### Cause

L'endpoint `/api/v1/learning/feedback` **requiert un token JWT** :

```python
@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackRequest,
    current_user: dict = Depends(get_current_user),  # ← Requiert token
):
```

**Mais** le frontend n'envoie pas le token dans cette requête.

### Analyse Technique

**Fichier problématique** : `frontend/src/services/api.js`

La fonction `submitFeedback()` ne doit pas inclure le token dans les headers.

**Erreur probable** :
```javascript
// api.js
export async function submitFeedback(feedbackData) {
  return axios.post('/api/v1/learning/feedback', feedbackData);
  // ❌ Pas de token envoyé
}
```

**Correction requise** :
```javascript
// api.js
export async function submitFeedback(feedbackData) {
  const token = localStorage.getItem('token');
  return axios.post('/api/v1/learning/feedback', feedbackData, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
}
```

### ✅ Solution (2 Options)

#### Option 1 : Ajouter Token dans Frontend (RECOMMANDÉ)

Modifier `frontend/src/services/api.js` pour envoyer le token.

**Avantage** : Respecte la sécurité (seuls les utilisateurs connectés peuvent donner feedback)

#### Option 2 : Rendre Endpoint Public

Modifier `backend/app/api/v1/learning.py` :

```python
@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_optional),  # ← Optional
):
```

**Avantage** : Fix rapide
**Inconvénient** : N'importe qui peut envoyer feedback (moins sécurisé)

### 🎯 Quelle Solution Voulez-Vous ?

**A.** Option 1 (frontend) - Sécurisé mais plus long
**B.** Option 2 (backend) - Rapide mais moins sécurisé
**C.** Les deux (frontend + fallback public)

---

## 📊 Impact Global

| Problème | Impact | Status | Urgence |
|----------|--------|--------|---------|
| **Hallucinations** | 🔴 CRITIQUE | ✅ Fix appliqué, test requis | HAUTE |
| **READMEs erronés** | 🟡 MOYEN | ⚠️ Fix prêt, attente approbation | MOYENNE |
| **Feedback cassé** | 🔴 CRITIQUE | ❌ Pas de fix appliqué | HAUTE |

---

## 🚀 Plan d'Action Immédiat

### Maintenant (Vous)

1. **Tester le fix hallucination** :
   - https://ai.4lb.ca
   - "Liste /home/projets"
   - Vérifier : pas d'inventions

2. **Décider pour README** :
   - Voulez-vous le fix ? (Oui/Non)

3. **Décider pour Feedback** :
   - Option A (frontend) ou B (backend) ?

### Après Vos Réponses (Moi)

1. Appliquer les fixes que vous choisissez
2. Redémarrer si nécessaire
3. Re-tester ensemble

---

## 💬 Questions Fréquentes

### Q: Pourquoi le fix hallucination ne marchait pas avant ?
**R**: Le backend n'avait pas rechargé le code Python. C'est maintenant corrigé.

### Q: C'est grave si les READMEs sont erronés ?
**R**: Moyen. L'AI répète de fausses infos, mais ça n'empêche pas le système de fonctionner.

### Q: Pourquoi le feedback ne fonctionne pas ?
**R**: Le frontend ne donne pas son "badge d'identité" (token JWT) au backend.

### Q: L'apprentissage stocke-t-il quand même des données ?
**R**: OUI ! ChromaDB enregistre automatiquement les expériences. Seul le feedback manuel (👍👎) est cassé.

---

## ✅ Prochaine Étape

**Dites-moi** :

1. ✅ ou ❌ : Test hallucination (après votre nouveau test)
2. Oui/Non : Appliquer fix README
3. A ou B : Solution pour feedback

Et je continue les corrections !

---

**Document créé** : 2026-01-26
**Status** : ⏳ EN ATTENTE DE VOS DÉCISIONS
