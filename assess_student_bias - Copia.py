import numpy as np
from scipy.stats import wilcoxon

# I tuoi dati (ho copiato le tue liste)
K_NS_Survey = [
    ("Advanced and persistent cyber threats (APT)", 0.575),
    ("Auditing standards, methodologies and frameworks", 0.45),
    ("Computer networks security", 0.975),
    ("Computer programming", 0.625),
    ("Computer Security Incident Response Teams (CSIRTs) operation", 0.6),
    ("Computer systems vulnerabilities", 0.85),
    ("Conformity assessment standards, methodologies and frameworks", 0.425),
    ("Criminal investigation procedures, standards, methodologies and frameworks", 0.45),
    ("Cross-domain and border-domain knowledge related to cybersecurity", 0.625),
    ("Cyber threat actors", 0.65),
    ("Cyber Threat Intelligence (CTI) sharing standards, methodologies and frameworks", 0.525),
    ("Cyber threats", 0.8),
    ("Cybersecurity attack procedures", 0.825),
    ("Cybersecurity awareness, education and training programme development", 0.675),
    ("Cybersecurity controls and solutions", 0.675),
    ("Cybersecurity maturity models", 0.5),
    ("Cybersecurity policies", 0.625),
    ("Cybersecurity procedures", 0.625),
    ("Cybersecurity recommendations and best practices", 0.8),
    ("Cybersecurity related laws, regulations and legislations", 0.45),
    ("Cybersecurity risks", 0.75),
    ("Cybersecurity standards, methodologies and frameworks", 0.625),
    ("Cybersecurity trends", 0.675),
    ("Cybersecurity-related certifications", 0.6),
    ("Cybersecurity-related requirements analysis", 0.625),
    ("Cybersecurity-related research, development and innovation (RDI)", 0.525),
    ("Cybersecurity-related technologies", 0.75),
    ("Digital forensics analysis procedures", 0.375),
    ("Digital forensics recommendations and best practices", 0.375),
    ("Digital forensics standards, methodologies and frameworks", 0.375),
    ("Ethical cybersecurity organisation requirements", 0.675),
    ("Incident handling communication procedures", 0.525),
    ("Incident handling recommendations and best practices", 0.575),
    ("Incident handling standards, methodologies and frameworks", 0.425),
    ("Incident handling tools", 0.45),
    ("Information technology (IT) and operational technology (OT) appliances", 0.575),
    ("Legacy cybersecurity procedures", 0.575),
    ("Legal, regulatory and legislative compliance requirements, recommendations and best practices", 0.45),
    ("Legal, regulatory and legislative requirements on releasing or using cybersecurity related technologies", 0.425),
    ("Malware analysis tools", 0.5),
    ("Monitoring, testing and evaluating cybersecurity controls' effectiveness", 0.6),
    ("Multidiscipline aspect of cybersecurity", 0.7),
    ("Offensive and defensive security practices", 0.925),
    ("Offensive and defensive security procedures", 0.925),
    ("Operating systems security", 0.55),
    ("Pedagogical standards, methodologies and frameworks", 0.4),
    ("Penetration testing procedures", 0.875),
    ("Penetration testing standards, methodologies and frameworks", 0.9),
    ("Penetration testing tools", 0.9),
    ("Privacy impact assessment standards, methodologies and frameworks", 0.45),
    ("Privacy-Enhancing Technologies (PET)", 0.425),
    ("Responsible information disclosure procedures", 0.575),
    ("Risk management recommendations and best practices", 0.5),
    ("Risk management standards, methodologies and frameworks", 0.475),
    ("Secure coding recommendations and best practices", 0.75),
    ("Secure development lifecycle", 0.55),
    ("Secure Operation Centres (SOCs) operation", 0.45),
    ("Security architecture reference models", 0.55),
    ("Testing procedures", 0.6),
    ("Testing standards, methodologies and frameworks", 0.55),
    ("Threat actors Tactics, Techniques and Procedures (TTPs)", 0.625)
]

K_NS_Survey_expert = [
    ("Advanced and persistent cyber threats (APT)", 0.5),
    ("Auditing standards, methodologies and frameworks", 0.45),
    ("Computer networks security", 0.9),
    ("Computer programming", 0.5),
    ("Computer Security Incident Response Teams (CSIRTs) operation", 0.5),
    ("Computer systems vulnerabilities", 0.7),
    ("Conformity assessment standards, methodologies and frameworks", 0.2),
    ("Criminal investigation procedures, standards, methodologies and frameworks", 0.2),
    ("Cross-domain and border-domain knowledge related to cybersecurity", 0.2),
    ("Cyber threat actors", 0.3),
    ("Cyber Threat Intelligence (CTI) sharing standards, methodologies and frameworks", 0.4),
    ("Cyber threats", 0.8),
    ("Cybersecurity attack procedures", 0.8),
    ("Cybersecurity awareness, education and training programme development", 0.2),
    ("Cybersecurity controls and solutions", 0.4),
    ("Cybersecurity maturity models", 0.2),
    ("Cybersecurity policies", 0.2),
    ("Cybersecurity procedures", 0.2),
    ("Cybersecurity recommendations and best practices", 0.5),
    ("Cybersecurity related laws, regulations and legislations", 0.3),
    ("Cybersecurity risks", 0.3),
    ("Cybersecurity standards, methodologies and frameworks", 0.4),
    ("Cybersecurity trends", 0.2),
    ("Cybersecurity-related certifications", 0.3),
    ("Cybersecurity-related requirements analysis", 0.2),
    ("Cybersecurity-related research, development and innovation (RDI)", 0.2),
    ("Cybersecurity-related technologies", 0.4),
    ("Digital forensics analysis procedures", 0.2),
    ("Digital forensics recommendations and best practices", 0.2),
    ("Digital forensics standards, methodologies and frameworks", 0.2),
    ("Ethical cybersecurity organisation requirements", 0.7),
    ("Incident handling communication procedures", 0.25),
    ("Incident handling recommendations and best practices", 0.25),
    ("Incident handling standards, methodologies and frameworks", 0.25),
    ("Incident handling tools", 0.25),
    ("Information technology (IT) and operational technology (OT) appliances", 0.4),
    ("Legacy cybersecurity procedures", 0.25),
    ("Legal, regulatory and legislative compliance requirements, recommendations and best practices", 0.25),
    ("Legal, regulatory and legislative requirements on releasing or using cybersecurity related technologies", 0.25),
    ("Malware analysis tools", 0.25),
    ("Monitoring, testing and evaluating cybersecurity controls' effectiveness", 0.6),
    ("Multidiscipline aspect of cybersecurity", 0.3),
    ("Offensive and defensive security practices", 0.8),
    ("Offensive and defensive security procedures", 0.8),
    ("Operating systems security", 0.3),
    ("Pedagogical standards, methodologies and frameworks", 0.1),
    ("Penetration testing procedures", 0.8),
    ("Penetration testing standards, methodologies and frameworks", 0.8),
    ("Penetration testing tools", 0.8),
    ("Privacy impact assessment standards, methodologies and frameworks", 0.25),
    ("Privacy-Enhancing Technologies (PET)", 0.3),
    ("Responsible information disclosure procedures", 0.2),
    ("Risk management recommendations and best practices", 0.2),
    ("Risk management standards, methodologies and frameworks", 0.2),
    ("Secure coding recommendations and best practices", 0.6),
    ("Secure development lifecycle", 0.35),
    ("Secure Operation Centres (SOCs) operation", 0.35),
    ("Security architecture reference models", 0.3),
    ("Testing procedures", 0.6),
    ("Testing standards, methodologies and frameworks", 0.3),
    ("Threat actors Tactics, Techniques and Procedures (TTPs)", 0.6)
]

# 1. Convertiamo in dizionari
student_dict = dict(K_NS_Survey)
expert_dict = dict(K_NS_Survey_expert)

# 2. Estraiamo chiavi comuni per allineamento sicuro
common_keys = sorted(list(set(student_dict.keys()).intersection(set(expert_dict.keys()))))

student_scores = []
expert_scores = []
differences = []

print("--- Student vs Expert Bias Analysis ---\n")

for key in common_keys:
    # Percentage conversion
    s_score = student_dict[key] * 100
    e_score = expert_dict[key] * 100
    diff = s_score - e_score
    
    student_scores.append(s_score)
    expert_scores.append(e_score)
    differences.append(diff)

student_scores = np.array(student_scores)
expert_scores = np.array(expert_scores)
differences = np.array(differences)

# 3. mean and standard deviation of differences
mean_diff = np.mean(differences)
std_diff = np.std(differences, ddof=1) # ddof=1 per sample standard deviation

print(f"Media della sovrastima (Overestimation Mean): +{mean_diff:.2f}%")
print(f"Deviazione Standard (SD): {std_diff:.2f}%")

# 4. (Wilcoxon Signed-Rank Test)
# alternative='greater' perché stiamo testando se gli studenti danno voti SIGNIFICATIVAMENTE maggiori
w_stat, p_value = wilcoxon(student_scores, expert_scores, alternative='greater')

print(f"Wilcoxon Test p-value: {p_value:.2e}")
if p_value < 0.05:
    print("-> RISULTATO: La sovrastima degli studenti è statisticamente significativa (p < 0.05). Non è un caso!")

# 5. Estrazione qualitativa (I Top e i Flop)
diff_tuples = [(key, student_dict[key]*100 - expert_dict[key]*100) for key in common_keys]
diff_tuples.sort(key=lambda x: x[1], reverse=True)

print("\n--- TOP 5 ARGOMENTI PIÙ SOVRASTIMATI (Bias alto) ---")
for t, d in diff_tuples[:5]:
    print(f"[{d:+.1f}%] {t} (Studenti: {student_dict[t]*100:.1f}%, Esperti: {expert_dict[t]*100:.1f}%)")

print("\n--- TOP 5 ARGOMENTI PIÙ ACCURATI (Bias nullo o basso) ---")
for t, d in reversed(diff_tuples[-5:]):
    print(f"[{d:+.1f}%] {t} (Studenti: {student_dict[t]*100:.1f}%, Esperti: {expert_dict[t]*100:.1f}%)")