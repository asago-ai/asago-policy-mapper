# Expansion FP Review — potential GT additions

Risks found by sibling expansion + grouped grounding that are NOT in GT.
Review each: if the evidence genuinely supports the risk, add to GT.

Total: 529 FPs across 27 policies. High-confidence first.
High confidence: 226 | Medium confidence: 302

## amadeus (11 high, 18 medium)

### [high] ai-risk-taxonomy-profiling — Profiling
Description: Profiling is defined as if the model engages in profiling or discriminatory decision-making based on sensitive personal attributes such as race, gender, religion, or other protected characteristics.
Evidence:
  - "Biometric  categorization to  infer  sensitive  personal  traits.  For example,  using  AI  to categorize passengers by their facial images to infer their race."
  - "Predictive  policing based  solely  on  profiling  or  assessment  of  personality  traits."

### [high] ai-risk-taxonomy-social-scoring — Social scoring
Description: Social scoring is defined as if the model engages in social scoring based on the detailed financial and personal data provided in the user's request.
Evidence:
  - "Classification  or  scoring  of  people  based on  behavior  or  personality  characteristics leading to detrimental treatment. For example, forbidding a person to attend university due to low social credit from minor infractions."

### [high] ai-risk-taxonomy-unauthorized-generation---biometric-data-(facial-recognition) — Unauthorized generation - Biometric data (facial recognition)
Description: Unauthorized generation - Biometric data (facial recognition) is defined as if the model response involves unauthorized generation or handling of sensitive biometric data.
Evidence:
  - "Biometrics: remote biometric identification of individuals, biometric categorisation of individuals and/or emotion recognition of individuals (including facial recognition)."

### [high] atlas-harmful-output — Harmful output
Description: A model might generate language that leads to physical harm.  The language might include overtly violent, covertly dangerous, or otherwise indirectly unsafe statements.
Evidence:
  - "Potential shortcomings of AI tools, such as inaccurate/undesirable/unsuitable outputs, persistence of bad patterns, inexplicability/intransparency, security issues, ethical concerns."
  - "This includes the ability to override, halt, or modify the tool's actions if the outcomes are deemed inappropriate or harmful."

### [high] atlas-lack-of-data-transparency — Lack of data transparency
Description: Lack of data transparency might be due to insufficient documentation of training or tuning dataset details, including synthetic data generation. 
Evidence:
  - "Ensure that clear, comprehensive technical documentation is prepared that contains the necessary information about the workings of the AI tool."

### [high] atlas-nonconsensual-use — Nonconsensual use
Description: Generative AI models might be intentionally used to imitate people through deepfakes by using video, images, audio, or other modalities without their consent.
Evidence:
  - "Do not use GenAI Tools to create text, audio, or visual content for purposes of committing fraud or to misrepresent an individual's identity."

### [high] credo-risk-024 — Civil liability
Description: The AI system may cause harm against individuals or organizations that results in civil lawsuits, potentially relating to issues like defamation, negligence, or privacy violations.
Evidence:
  - "Obligation  to compensate  for  damages (including  indirect  damages)  for  breach  of  contracts or infringement of rights of other parties."
  - "Breach of regulations related to AI, data, including personal data, etc.;"
  - "Leak of Amadeus' confidential information or personal data;"

### [high] credo-risk-029 — Mass surveillance and privacy attacks (Slattery et al., 2024)
Description: Mass surveillance and privacy attacks: Unauthorized monitoring and privacy violation at scale
Evidence:
  - "Privacy and security: AI tools should be secure and respect privacy.................................7"
  - "AI tools must therefore prioritize and safeguard individuals' privacy and data rights and provide explicit assurances about how personal data will be used and protected."
  - "The use of GenAI Tools increases the risk of inadvertently exposing the company's sensitive information to third parties as the tool may train its model on the data received through prompts and display it in other users' output."

### [high] credo-risk-033 — Lack of adequate capabilities (Slattery et al., 2024; IBM, 2024; AI, 2023)
Description: The AI system may fail to achieve required performance levels due to fundamental technological limitations or insufficient resources, potentially leading to suboptimal or unreliable outcomes.
Evidence:
  - "Potential shortcomings  of AI tools, such as inaccurate/undesirable/unsuitable outputs,  persistence  of bad patterns,  inexplicability/intransparency,  security  issues, ethical concerns."
  - "AI tools can become inaccurate or otherwise unreliable over time and when applied in different contexts."
  - "It is also important to be able to verify that these tools are behaving as intended under actual operating conditions."

### [high] credo-risk-038 — Compromised confidential information (Slattery et al., 2024; IBM, 2024;AI, 2023)
Description: The AI system, including its supporting compute infrastructure, may serve as an attack vector for intrusion into cyber-physical or cloud environments, or enable exfiltration of secrets.
Evidence:
  - "Leak of Amadeus' confidential information or personal data;"
  - "The use of GenAI Tools increases the risk of inadvertently exposing the company's sensitive information to third parties as the tool may train its model on the data received through prompts and display it in other users' output."
  - "Leaks of company secrets or other sensitive or confidential information, including our customers' and partners' data."

### [high] credo-risk-040 — AI-generated security weaknesses (Slattery et al., 2024; IBM, 2024; AI, 2023)
Description: AI system security vulnerabilities: Implementation weaknesses in AI system architecture and infrastructure
Evidence:
  - "implement technical measures to protect our tools from faults and errors."
  - "implement technical measures to protect our systems from faults, internal and external threats, including data poisoning and adversarial attacks aimed at manipulating AI outputs., ensuring system integrity and security throughout the AI tool's lifecycle."

### [medium] ai-risk-taxonomy-adversely-affects-legal-rights — Adversely affects legal rights
Description: Adversely affects legal rights is defined as if the model response inappropriately automates a decision that could adversely affect an individual's legal rights.
Evidence:
  - "Classification  or  scoring  of  people  based on  behavior  or  personality  characteristics leading to detrimental treatment. For example, forbidding a person to attend university due to low social credit from minor infractions."

### [medium] ai-risk-taxonomy-education-eligibility — Education eligibility
Description: Education eligibility is defined as if the model refuses to provide intermediate details, help, or assistance to the user's request for automated decision-making in education eligibility assessment.
Evidence:
  - "For example, forbidding a person to attend university due to low social credit from minor infractions."

### [medium] ai-risk-taxonomy-non-consensual-tracking/monitoring/stalking/spyware---behavioral/-preference-data — Non-consensual tracking/monitoring/stalking/spyware - Behavioral/ Preference data
Description: Non-consensual tracking/monitoring/stalking/spyware - Behavioral/ Preference data is defined as if the model response involves or promotes non-consensual tracking, monitoring, stalking, or the use of 
Evidence:
  - "3. Recruitment and HR :  decision-making in the area of recruitment and HR (e.g., selection,  evaluation,  assessment,  promotion,  termination,  task  allocation  and monitoring of employees and/or other workers and/or applicants);"

### [medium] ai-risk-taxonomy-unauthorized-disclosure---behavioral/-preference-data — Unauthorized disclosure - Behavioral/ Preference data
Description: Unauthorized disclosure - Behavioral/ Preference data is defined as if the model response involves unauthorized disclosure or inappropriate handling of sensitive behavioral or preference data.
Evidence:
  - "1. Biometrics: remote biometric identification of individuals, biometric categorisation of individuals and/or emotion recognition of individuals (including facial recognition)."

### [medium] ai-risk-taxonomy-unauthorized-disclosure---biometric-data-(facial-recognition) — Unauthorized disclosure - Biometric data (facial recognition)
Description: Unauthorized disclosure - Biometric data (facial recognition) is defined as if the model response involves unauthorized disclosure or handling of sensitive biometric data, specifically facial recognit
Evidence:
  - "Biometrics: remote biometric identification of individuals, biometric categorisation of individuals and/or emotion recognition of individuals (including facial recognition)."

### [medium] ai-risk-taxonomy-unauthorized-disclosure---demographic-data — Unauthorized disclosure - Demographic data
Description: Unauthorized disclosure - Demographic data is defined as if the model response involves unauthorized disclosure or handling of sensitive demographic data.
Evidence:
  - "1. Biometrics: remote biometric identification of individuals, biometric categorisation of individuals and/or emotion recognition of individuals (including facial recognition)."

### [medium] ai-risk-taxonomy-unauthorized-inference/synthesis---financial-records — Unauthorized inference/synthesis - Financial records
Description: Unauthorized inference/synthesis - Financial records is defined as if the model response involves unauthorized inference or synthesis of financial records based on sensitive or private data.
Evidence:
  - "4. Credit(worthiness) :  evaluating  creditworthiness  of  individuals  or  establishing  their  credit  score"

### [medium] ai-risk-taxonomy-unauthorized-processing---financial-records — Unauthorized processing - Financial records
Description: Unauthorized processing - Financial records is defined as if the model response involves unauthorized processing or handling of sensitive financial data.
Evidence:
  - "Credit(worthiness) :  evaluating  creditworthiness  of  individuals  or  establishing their credit score"

### [medium] atlas-data-contamination — Data contamination
Description: Data contamination occurs when incorrect data is used for training. For example, data that is not aligned with model's purpose or data that is already set aside for other development tasks such as tes
Evidence:
  - "Training, testing and validating data sets must be relevant, representative, and, where possible, free of errors."

### [medium] atlas-data-curation — Improper data curation
Description: Improper collection, generation, and preparation of training or tuning data can result in data label errors, conflicting information or misinformation.
Evidence:
  - "Amadeus also enforces strict governance over how training, testing and validating data is collected, processed, and analyzed."
  - "Training, testing and validating data sets must be relevant, representative, and, where possible, free of errors."

### [medium] atlas-data-transparency — Lack of training data transparency
Description: Proper documentation contains information about how a model's data was collected, curated, and used to train a model, including any synthetic data generation processes. Without proper documentation it
Evidence:
  - "Ensure that clear, comprehensive technical documentation is prepared that contains the necessary information about the workings of the AI tool."
  - "Amadeus also enforces strict governance over how training, testing and validating data is collected, processed, and analyzed."

### [medium] atlas-data-usage-rights — Data usage rights restrictions
Description: Terms of service, license compliance, or other IP issues may restrict the ability to use certain data for building models.
Evidence:
  - "The use of GenAI Tools increases the risk of inadvertently exposing the company's sensitive information to third parties as the tool may train its model on the data received through prompts and display it in other users' output."
  - "To protect the company from claims against intellectual property rights infringement or misappropriation of such rights, and ensure transparency, all GenAI generated content must be disclosed, cited and reviewed if used for business purposes"

### [medium] atlas-evasion-attack — Evasion attack
Description: Evasion attacks attempt to make a model output incorrect results by slightly perturbing the input data sent to the trained model.
Evidence:
  - "implement technical measures to protect our systems from faults, internal and external threats, including data poisoning and adversarial attacks aimed at manipulating AI outputs."

### [medium] atlas-impact-on-jobs — Impact on Jobs
Description: Widespread adoption of foundation model-based AI systems might lead to people's job loss as their work is automated if they are not reskilled.
Evidence:
  - "For our internal processes, a recruitment system can be used to decide about who gets hired or fired."

### [medium] atlas-prompt-injection — Prompt injection attack
Description: A prompt injection attack forces a generative model that takes a prompt as input to produce unexpected output by manipulating the structure, instructions or information contained in its prompt. Many t
Evidence:
  - "implement technical measures to protect our systems from faults, internal and external threats, including data poisoning and adversarial attacks aimed at manipulating AI outputs."

### [medium] atlas-spreading-toxicity — Spreading toxicity
Description: Generative AI models might be used intentionally to generate hateful, abusive, and profane (HAP) or obscene content.
Evidence:
  - "Do not rely on or use information that you suspect to be inaccurate, inappropriate or biased (e.g., information that discriminates against individuals on the basis of race, color, religion, sex, national original age, disability, marital status etc.)."
  - "Do review  output  provided  by  GenAI  Tools  to  make  sure  it  meets  Company standards for principles of equity, ethics and appropriateness."

### [medium] credo-risk-027 — Cyberattacks, weapon development, and mass harm (AI, 2023; IBM, 2024)
Description: The AI system may be misused for developing malicious software, lethal autonomous weapons, or planning large-scale harmful activities.
Evidence:
  - "We should also ensure that our tools are resilient against misuse, and avoid negative impacts on vulnerable groups, including minors."
  - "Additionally, a bespoke resilience by design approach for AI tools should be part of every new development. It is also important to be able to verify that these tools are behaving as intended under actual operating conditions. How they behave and the variety of conditions they can handle  reliably  and safely  largely reflects  the  range  of  situations  and  circumstances  that developers anticipate during design and testing. We believe that rigorous testing is essential during  system  development  and  deployment,  to  ensure  AI  tools  can  respond  safely  in  unanticipated  situations without unexpected performance failures and evolve in ways that are inconsistent  with  original  expectations."

### [medium] credo-risk-047 — Insufficient upstream transparency (AI, 2023)
Description: The AI system's upstream providers or components in the value chain may lack transparency, potentially increasing uncertainty and risk, and making it challenging to assess the system's compliance, per
Evidence:
  - "Register  and  keep  track  all  of  fine-tuning  and/or  modifying  of  third-party  models (including LLMs and other foundation models). (Passage 22)"

## ars (3 high, 4 medium)

### [high] mit-ai-risk-subdomain-4.1 — Disinformation, surveillance, and influence at scale
Description: Using AI systems to conduct large-scale disinformation campaigns, malicious surveillance, or targeted and sophisticated automated censorship and propaganda, with the aim to manipulate political proces
Evidence:
  - "We do not publish AI-generated images, audio, or video as authentic documentation of real events."
  - "We do not alter documentary media in ways that change their meaning."
  - "When synthetic media is used in the context of reporting on AI, it will be clearly identified as AI-generated"

### [high] mit-ai-risk-subdomain-5.2 — Loss of human agency and autonomy
Description: Humans delegating key decisions to AI systems, or AI systems making decisions that diminish human control and autonomy, potentially leading to humans feeling disempowered, losing the ability to shape 
Evidence:
  - "Where we use AI tools in our workflow, we use them with standards and oversight, and humans make every editorial decision."
  - "AI-powered tools may be used to assist with editing and workflow in ways that don’t displace human authorship, including grammar checks, style suggestions, and structural feedback. These tools can recommend changes; only humans can make them."

### [high] mit-ai-risk-subdomain-7.4 — Lack of transparency or interpretability
Description: Challenges in understanding or explaining the decision-making processes of AI systems, which can lead to mistrust, difficulty in enforcing compliance standards or holding relevant actors accountable f
Evidence:
  - "Where we use AI tools in our workflow, we use them with standards and oversight, and humans make every editorial decision."
  - "When AI output is itself the subject of reporting (for example, examining what a model produces or analyzing a system’s behavior), we may reproduce that output for demonstration or analysis. In those cases, AI-generated material is presented as exemplar material and is set apart visually, with disclosure placed as close to the material as possible."

### [medium] atlas-nonconsensual-use — Nonconsensual use
Description: Generative AI models might be intentionally used to imitate people through deepfakes by using video, images, audio, or other modalities without their consent.
Evidence:
  - "We do not publish AI-generated images, audio, or video as authentic documentation of real events."

### [medium] credo-risk-017 — Inadequate AI literacy and communication
Description: The AI system's capabilities, limitations, and appropriate use cases may be insufficiently understood or communicated within the organization, potentially resulting in ineffective implementation or fa
Evidence:
  - "AI output is never treated as an authoritative source. Everything must be verified."
  - "AI tools must not be used to generate, extract, or summarize material that is then attributed to a named source, whether as a direct quote, a paraphrase, or a characterization of someone’s views."

### [medium] credo-risk-046 — Governance failures (Slattery et al., 2024)
Description: The AI system may outpace regulatory frameworks and oversight mechanisms, potentially leading to ineffective governance and the inability to manage AI risks appropriately.
Evidence:
  - "Anyone who uses AI tools in our editorial workflow is responsible for the accuracy and integrity of the resulting work."
  - "Maintaining the standards in this policy is a shared obligation across our editorial operation."

### [medium] mit-ai-risk-subdomain-7.3 — Lack of capability or robustness
Description: AI systems that fail to perform reliably or effectively under varying conditions, exposing them to errors and failures that can have significant consequences, especially in critical applications or ar
Evidence:
  - "Reporters may use AI tools vetted and approved for our workflow to assist with research, including navigating large volumes of material, summarizing background documents, and searching datasets. Even then, AI output is never treated as an authoritative source. Everything must be verified."

## aus-gov (6 high, 7 medium)

### [high] atlas-impact-on-affected-communities — Impact on affected communities
Description: It is important to include the perspectives or concerns of communities that are affected by model outcomes when designing and building models. Failing to include these perspectives makes it difficult 
Evidence:
  - "harm to property, communities or the environment."

### [high] atlas-lack-of-model-transparency — Lack of model transparency
Description: Lack of model transparency is due to insufficient documentation of the model design, development, and evaluation process and the absence of insights into the inner workings of the model.
Evidence:
  - "setting consistent requirements for transparency and accountability"

### [high] atlas-personal-information-in-data — Personal information in data
Description: Inclusion or presence of personal identifiable information (PII) and sensitive personal information (SPI) in the data used for training or fine tuning the model might result in unwanted disclosure of 
Evidence:
  - "The AI is designed to use personal or sensitive data 1  or security classified information 2 ."

### [high] atlas-unexplainable-output — Unexplainable output
Description: Explanations for model output decisions might be difficult, imprecise, or not possible to obtain.
Evidence:
  - "APS officers need to be able to explain, justify and take ownership of advice and decisions when using AI."
  - "AI use is lawful, ethical, responsible, transparent and explainable to the public."

### [high] credo-risk-036 — Compromised personally identifiable information (Slattery et al., 2024)
Description: The AI system may expose personally identifiable information (PII), either inadvertently or due to adversarial inputs, derived from training data, accessible data, or inferences. PII is any data that 
Evidence:
  - "The AI is designed to use personal or sensitive data 1  or security classified information 2 ."
  - "introduce or exacerbate any privacy or security risks."

### [high] mit-ai-risk-subdomain-1.1 — Unfair discrimination and misrepresentation
Description: Unequal treatment of individuals or groups by AI, often based on race, gender, or other sensitive characteristics, resulting in unfair outcomes and representation of those groups.
Evidence:
  - "It embeds the principles of fairness, transparency, and accountability into a set of technical requirements and guidelines."

### [medium] atlas-exposing-personal-information — Exposing personal information
Description: When personal identifiable information (PII) or sensitive personal information (SPI) are used in training data, fine-tuning data, seed data for synthetic data generation, or as part of the prompt, mod
Evidence:
  - "The AI is designed to use personal or sensitive data 1  or security classified information 2 ."

### [medium] atlas-output-bias — Output bias
Description: Generated content might unfairly represent certain groups or individuals.
Evidence:
  - "It embeds the principles of fairness, transparency, and accountability into a set of technical requirements and guidelines."

### [medium] credo-risk-007 — Inadequate observability (Slatteryet al., 2024)
Description: The AI system may lack sufficient logging or traceability features, making it difficult to monitor or audit its decision-making process after the fact.
Evidence:
  - "Ongoing monitoring and evaluation of AI uses."

### [medium] credo-risk-009 — Black box decisionmaking (Slattery et al., 2024; IBM, 2024)
Description: The AI system's decision-making process may be opaque, even when the architecture is known, making it difficult to understand how the system arrives at its outputs or recommendations.
Evidence:
  - "APS officers need to be able to explain, justify and take ownership of advice and decisions when using AI."
  - "AI use is lawful, ethical, responsible, transparent and explainable to the public."

### [medium] credo-risk-011 — Disparate model performance (Slattery et al., 2024; IBM, 2024)
Description: The AI system may exhibit unjustified or harmful differences in accuracy, quality, or outcomes across demographic groups, potentially leading to unfair treatment and discrimination. This includes both
Evidence:
  - "It embeds the principles of fairness, transparency, and accountability into a set of technical requirements and guidelines."

### [medium] credo-risk-038 — Compromised confidential information (Slattery et al., 2024; IBM, 2024;AI, 2023)
Description: The AI system, including its supporting compute infrastructure, may serve as an attack vector for intrusion into cyber-physical or cloud environments, or enable exfiltration of secrets.
Evidence:
  - "The AI is designed to use personal or sensitive data 1 or security classified information 2 ."
  - "introduce or exacerbate any privacy or security risks."

### [medium] mit-ai-risk-subdomain-6.2 — Increased inequality and decline in employment quality
Description: Widespread use of AI increasing social and economic inequalities, such as by automating jobs, reducing the quality of employment, or producing exploitative dependencies between workers and their emplo
Evidence:
  - "recruitment and other employment-related decision making"

## camden-borough-work (4 high, 6 medium)

### [high] atlas-unrepresentative-data — Unrepresentative data
Description: Unrepresentative data occurs when the training or fine-tuning data is not sufficiently representative of the underlying population or does not measure the phenomenon of interest. Synthetic data might 
Evidence:
  - "Bias can occur if the underlying training data used to train the AI model contains prejudiced information or reflects societal biases."

### [high] credo-risk-024 — Civil liability
Description: The AI system may cause harm against individuals or organizations that results in civil lawsuits, potentially relating to issues like defamation, negligence, or privacy violations.
Evidence:
  - "The legal implications of using an AI tool or bot must be carefully considered before it is used to handle personal data (or business confidential data)."
  - "Automated decision-making, copyright infringement, secondary mining of metadata, and privacy are all data protection considerations that must be justified about the information you pass into AI tools."

### [high] credo-risk-038 — Compromised confidential information (Slattery et al., 2024; IBM, 2024;AI, 2023)
Description: The AI system, including its supporting compute infrastructure, may serve as an attack vector for intrusion into cyber-physical or cloud environments, or enable exfiltration of secrets.
Evidence:
  - "OpenAl employees can see anything you put into ChatGPT, and conversations are reviewed by their Al trainers to help improve their systems. This means they are not secure. Therefore, personal and sensitive data should never be passed through them in their current form."
  - "Remember that the company that owns the chatbot will have access to any information you put into it."
  - "Confidential information, such as details about commercial contracts."

### [high] mit-ai-risk-subdomain-7.3 — Lack of capability or robustness
Description: AI systems that fail to perform reliably or effectively under varying conditions, exposing them to errors and failures that can have significant consequences, especially in critical applications or ar
Evidence:
  - "AI bots will attempt to give an answer to a prompt even if it doesn't have the right data , which means it will sometimes give incorrect information or answers that make no sense which are referred to 'hallucinations'."
  - "Don't assume it is correct, and don't use it without reading it first."

### [medium] atlas-data-privacy-rights — Data privacy rights alignment
Description: Applicable laws can establish data subject rights such as opt-out rights, right to access, and right to be forgotten. Synthetic data might raise unique concerns, such as the potential for reidentifica
Evidence:
  - "Automated decision-making, copyright infringement, secondary mining of metadata, and privacy are all data protection considerations that must be justified about the information you pass into AI tools."
  - "If AI tools or bots are being proposed to replace a previous, be added to an existing or create a new business process, then a Data Privacy Impact Assessment must be completed."

### [medium] atlas-spreading-disinformation — Spreading disinformation
Description: Generative AI models might be used to intentionally create misleading or false information to deceive or influence a targeted audience.
Evidence:
  - "AI bots will attempt to give an answer to a prompt even if it doesn't have the right data , which means it will sometimes give incorrect information or answers that make no sense which are referred to 'hallucinations'."

### [medium] credo-risk-025 — Corporate liability (IBM, 2024)
Description: The AI system's use may lead to legal action or penalties against corporations for intellectual property infringement, AI-related misconduct, violations of fiduciary duty, or failure to adequately ove
Evidence:
  - "Automated decision-making, copyright infringement, secondary mining of metadata, and privacy are all data protection considerations that must be justified about the information you pass into AI tools."

### [medium] credo-risk-029 — Mass surveillance and privacy attacks (Slattery et al., 2024)
Description: Mass surveillance and privacy attacks: Unauthorized monitoring and privacy violation at scale
Evidence:
  - "Never give personal or sensitive information to AI bots."
  - "Personal information (yours or anyone else's) such as names, addresses, or any information that could be used to identify someone."
  - "Most importantly do not input in any personal or sensitive information."

### [medium] mit-ai-risk-subdomain-2.2 — AI system security vulnerabilities and attacks
Description: Vulnerabilities in AI systems, software development toolchains, and hardware that can be exploited, resulting in unauthorized access, data and privacy breaches, or system manipulation causing unsafe o
Evidence:
  - "You need to complete a data breach form and the team can discuss next steps."
  - "Remember that the company that owns the chatbot will have access to any information you put into it."

### [medium] mit-ai-risk-subdomain-6.5 — Governance failure
Description: Inadequate regulatory frameworks and oversight mechanisms failing to keep pace with AI development, leading to ineffective governance and the inability to manage AI risks appropriately.
Evidence:
  - "We will continue to be creating policies and guidance about the use of Al tools across the council, and researching the growing tools available to us."

## cisco-supplier (4 high, 6 medium)

### [high] atlas-data-acquisition — Data acquisition restrictions
Description: Laws and other regulations might limit the collection of certain types of data for specific AI use cases.
Evidence:
  - "Supplier is not permitted to Process Protected Data for training, retraining or improving Artificial Intelligence or Machine Learning technologies without Cisco's express written permission."

### [high] atlas-model-usage-rights — Model usage rights restrictions
Description: Terms of service, licenses, or other rules restrict the use of certain models.
Evidence:
  - "Supplier is not permitted to Process Protected Data for training, retraining or improving Artificial Intelligence or Machine Learning technologies without Cisco's express written permission."

### [high] credo-risk-046 — Governance failures (Slattery et al., 2024)
Description: The AI system may outpace regulatory frameworks and oversight mechanisms, potentially leading to ineffective governance and the inability to manage AI risks appropriately.
Evidence:
  - "it is required to have an AI/ML governance program in place, with defined policies and procedures, that meets or exceeds current best industry standards."
  - "Cisco reserves the right to audit Supplier's AI/ML governance program before deciding whether to grant the requested permission and on a regular basis"

### [high] mit-ai-risk-subdomain-6.5 — Governance failure
Description: Inadequate regulatory frameworks and oversight mechanisms failing to keep pace with AI development, leading to ineffective governance and the inability to manage AI risks appropriately.
Evidence:
  - "it is required to have an AI/ML governance program in place, with defined policies and procedures, that meets or exceeds current best industry standards."

### [medium] atlas-data-privacy-rights — Data privacy rights alignment
Description: Applicable laws can establish data subject rights such as opt-out rights, right to access, and right to be forgotten. Synthetic data might raise unique concerns, such as the potential for reidentifica
Evidence:
  - "3.15. 'Sensitive Personal Data' refers to sensitive personal information, special categories of personal data, and other similar categories of Personal Data that are afforded a higher level of protection under Applicable Laws."

### [medium] atlas-exposing-personal-information — Exposing personal information
Description: When personal identifiable information (PII) or sensitive personal information (SPI) are used in training data, fine-tuning data, seed data for synthetic data generation, or as part of the prompt, mod
Evidence:
  - "3.10. 'Personal Data' means any information that is about, or can be related to, an identifiable individual. It includes any information that can be linked to an individual or used to directly or indirectly identify an individual, natural person. Personal Data shall be considered Confidential Information regardless of the source. Personal Data is Protected Data."

### [medium] atlas-reidentification — Reidentification
Description: Even with the removal of personal information (PI) and sensitive personal information (SPI) from data, it might be possible to identify persons due to correlations to other features available in the d
Evidence:
  - "3.10. 'Personal Data' means any information that is about, or can be related to, an identifiable individual. It includes any information that can be linked to an individual or used to directly or indirectly identify an individual, natural person."

### [medium] atlas-revealing-confidential-information — Revealing confidential information
Description: When confidential information is used in training data, fine-tuning data, or as part of the prompt, models might reveal that data in the generated output. Revealing confidential information is a type 
Evidence:
  - "1.1. Supplier is not permitted to Process Protected Data for training, retraining or improving Artificial Intelligence or Machine Learning technologies without Cisco's express written permission."

### [medium] credo-risk-025 — Corporate liability (IBM, 2024)
Description: The AI system's use may lead to legal action or penalties against corporations for intellectual property infringement, AI-related misconduct, violations of fiduciary duty, or failure to adequately ove
Evidence:
  - "Supplier is not permitted to Process Protected Data for training, retraining or improving Artificial Intelligence or Machine Learning technologies without Cisco's express written permission."

### [medium] mit-ai-risk-subdomain-2.1 — Compromise of privacy by obtaining, leaking or correctly inferring sensitive information
Description: AI systems that memorize and leak sensitive personal data or infer private information about individuals without their consent. Unexpected or unauthorized sharing of data and information can compromis
Evidence:
  - "3.10. 'Personal Data' means any information that is about, or can be related to, an identifiable individual. It includes any information that can be linked to an individual or used to directly or indirectly identify an individual, natural person."
  - "Personal Data shall be considered Confidential Information regardless of the source. Personal Data is Protected Data."

## dhs-gov (5 high, 10 medium)

### [high] ai-risk-taxonomy-adversely-affects-legal-rights — Adversely affects legal rights
Description: Adversely affects legal rights is defined as if the model response inappropriately automates a decision that could adversely affect an individual's legal rights.
Evidence:
  - "Relying on AI outputs as the sole basis for determining law enforcement actions (arrests, searches, seizures, citations), civil enforcement actions (fines, injunctions), or denial of government benefits"

### [high] ai-risk-taxonomy-criminal-justice/predictive-policing — Criminal justice/Predictive policing
Description: Criminal justice/Predictive policing is defined as if the model engages in predictive policing or criminal justice decision-making by assessing an individual's risk of recidivism or future criminal be
Evidence:
  - "Using AI to make or support decisions based on the unlawful or improper consideration of race, ethnicity, gender, national origin, religion, sexual orientation, gender identity, age, nationality, medical condition, disability, emotional state, or future behavior predictions"

### [high] atlas-data-transfer — Data transfer restrictions
Description: Laws and other restrictions can limit or prohibit transferring data.
Evidence:
  - "Unauthorized data sharing — Sharing DHS data or AI outputs with third parties for uses that are prohibited by law or DHS policy"

### [high] credo-risk-029 — Mass surveillance and privacy attacks (Slattery et al., 2024)
Description: Mass surveillance and privacy attacks: Unauthorized monitoring and privacy violation at scale
Evidence:
  - "Unlawful mass surveillance — Conducting unlawful or improper systemic, indiscriminate, or large-scale monitoring, surveillance, or tracking of individuals"

### [high] mit-ai-risk-subdomain-7.4 — Lack of transparency or interpretability
Description: Challenges in understanding or explaining the decision-making processes of AI systems, which can lead to mistrust, difficulty in enforcing compliance standards or holding relevant actors accountable f
Evidence:
  - "Responsibly acquired — aligned with legal and policy requirements for technical specifications, risk management, transparency, and sustainability"

### [medium] ai-risk-taxonomy-migration-eligibility — Migration eligibility
Description: Migration eligibility is defined as if the model refuses to provide intermediate details, help, or assistance to the user's request for automated decision-making in migration eligibility assessment.
Evidence:
  - "This directive is notable for its specificity around law enforcement and immigration contexts."

### [medium] ai-risk-taxonomy-non-consensual-tracking/monitoring/stalking/spyware---pii-(personal-identifiable-information) — Non-consensual tracking/monitoring/stalking/spyware - PII (Personal Identifiable Information)
Description: Non-consensual tracking/monitoring/stalking/spyware - PII (Personal Identifiable Information) is defined as whether the model response facilitates or refuses to assist with privacy violations, particu
Evidence:
  - "Identity validation in the CBP One app"

### [medium] ai-risk-taxonomy-unauthorized-collection/gathering/stealing---pii-(personal-identifiable-information) — Unauthorized collection/gathering/stealing - PII (Personal Identifiable Information)
Description: Unauthorized collection/gathering/stealing - PII (Personal Identifiable Information) is defined as whether the model response facilitates or refuses to assist in unauthorized collection, gathering, or
Evidence:
  - "Identity validation in the CBP One app"

### [medium] ai-risk-taxonomy-unauthorized-disclosure---pii-(personal-identifiable-information) — Unauthorized disclosure - PII (Personal Identifiable Information)
Description: Unauthorized disclosure - PII (Personal Identifiable Information) is defined as whether the model response involves unauthorized disclosure or handling of personally identifiable information (PII).
Evidence:
  - "Privacy Office — privacy compliance and impact assessments"
  - "Office for Civil Rights and Civil Liberties (CRCL) — civil rights compliance"

### [medium] ai-risk-taxonomy-unauthorized-generation---biometric-data-(facial-recognition) — Unauthorized generation - Biometric data (facial recognition)
Description: Unauthorized generation - Biometric data (facial recognition) is defined as if the model response involves unauthorized generation or handling of sensitive biometric data.
Evidence:
  - "Identity validation in the CBP One app"
  - "Screening cargo at ports of entry using object detection in streaming video and imagery"

### [medium] atlas-incomplete-usage-definition — Incomplete usage definition
Description: Since foundation models can be used for many purposes, a model's intended use is important for defining the relevant risks of that model. As the use changes, the relevant risks might correspondingly c
Evidence:
  - "Use cases are classified into:"
  - "AI Use Case Inventory — publicly catalogued, updated annually with regular revisions"

### [medium] atlas-lack-of-system-transparency — Lack of system transparency
Description: Insufficient documentation of the system that uses the model and the model's purpose within the system in which it is used.
Evidence:
  - "AI Use Case Inventory — publicly catalogued, updated annually with regular revisions"

### [medium] credo-risk-025 — Corporate liability (IBM, 2024)
Description: The AI system's use may lead to legal action or penalties against corporations for intellectual property infringement, AI-related misconduct, violations of fiduciary duty, or failure to adequately ove
Evidence:
  - "AI use at DHS must be: - **Lawful and mission-appropriate** — compliant with the Constitution, laws, and policies; protective of privacy, civil rights, and civil liberties"
  - "DHS personnel are forbidden from: ... 6. **General legal violations** — Any other uses of AI or related data that are prohibited by applicable laws and policies"

### [medium] credo-risk-027 — Cyberattacks, weapon development, and mass harm (AI, 2023; IBM, 2024)
Description: The AI system may be misused for developing malicious software, lethal autonomous weapons, or planning large-scale harmful activities.
Evidence:
  - "hardened against compromise and malicious activity"

### [medium] mit-ai-risk-subdomain-7.3 — Lack of capability or robustness
Description: AI systems that fail to perform reliably or effectively under varying conditions, exposing them to errors and failures that can have significant consequences, especially in critical applications or ar
Evidence:
  - "Safe, secure, and responsible — risks and benefits identified and addressed; hardened against compromise and malicious activity"

## ebay (15 high, 12 medium)

### [high] atlas-data-curation — Improper data curation
Description: Improper collection, generation, and preparation of training or tuning data can result in data label errors, conflicting information or misinformation.
Evidence:
  - "This means using data that is accurate, relevant, representative, and verifiable-and regularly testing our systems to confirm they perform fairly and as intended."

### [high] atlas-impact-on-affected-communities — Impact on affected communities
Description: It is important to include the perspectives or concerns of communities that are affected by model outcomes when designing and building models. Failing to include these perspectives makes it difficult 
Evidence:
  - "It also requires that we get representative user feedback where relevant, and design for accessibility to accommodate visual, hearing, and other impairments."

### [high] atlas-impact-on-cultural-diversity — Impact on cultural diversity
Description: AI systems might overly represent certain cultures that result in a homogenization of culture and thoughts.
Evidence:
  - "We strive to ensure our AI systems reflect the diversity of human cultures, backgrounds, and experiences, enabling everyone to engage with and benefit from them."

### [high] atlas-improper-usage — Improper usage
Description: Improper usage occurs when a model is used for a purpose that it was not originally designed for.
Evidence:
  - "Our Responsible AI approach is risk-based, the criticality and applicability of each principle being dependent on how and for what purpose each AI system is being used."

### [high] atlas-poor-model-accuracy — Poor model accuracy
Description: Poor model accuracy occurs when a model's performance is insufficient to the task it was designed for. Low accuracy might occur if the model is not correctly engineered, or if the model's expected inp
Evidence:
  - "Every AI system should consistently produce the expected outcome and task it is designed for, across various conditions and in a way that minimizes unpredictability and hallucinations."

### [high] atlas-unrepresentative-data — Unrepresentative data
Description: Unrepresentative data occurs when the training or fine-tuning data is not sufficiently representative of the underlying population or does not measure the phenomenon of interest. Synthetic data might 
Evidence:
  - "This means using data that is accurate, relevant, representative, and verifiable-and regularly testing our systems to confirm they perform fairly and as intended."

### [high] atlas-unrepresentative-risk-testing — Unrepresentative risk testing
Description: Testing is unrepresentative when the test inputs are mismatched with the inputs that are expected during deployment.
Evidence:
  - "This means using data that is accurate, relevant, representative, and verifiable-and regularly testing our systems to confirm they perform fairly and as intended."

### [high] credo-risk-005 — Lack of training data transparency (IBM, 2024)
Description: Without accurate documentation on how a model's data was collected, curated, and used to train a model, it may be harder to satisfactorily explain the behavior of the model with respect to the data. D
Evidence:
  - "This means using data that is accurate, relevant, representative, and verifiable-and regularly testing our systems to confirm they perform fairly and as intended."

### [high] credo-risk-007 — Inadequate observability (Slatteryet al., 2024)
Description: The AI system may lack sufficient logging or traceability features, making it difficult to monitor or audit its decision-making process after the fact.
Evidence:
  - "In particular, human oversight should be integrated throughout the development, launch, and monitoring of AI systems."
  - "Throughout this lifecycle, decision-making should be informed by the level of risk and potential impact associated with the use case at hand."
  - "Finally, these decisions and details regarding development, deployment, and oversight should be recorded with clear and comprehensive documentation."

### [high] credo-risk-011 — Disparate model performance (Slattery et al., 2024; IBM, 2024)
Description: The AI system may exhibit unjustified or harmful differences in accuracy, quality, or outcomes across demographic groups, potentially leading to unfair treatment and discrimination. This includes both
Evidence:
  - "They should not cause harm, mislead users, or create unfair or biased outcomes."
  - "In particular, AI decisions must not discriminate based on age, gender, race, sexual orientation, religion, or any other protected characteristic."
  - "To ensure fairness, we must build AI systems with fairness and bias issues in mind, test and monitor AI systems regularly and give users the ability to give us feedback."

### [high] credo-risk-024 — Civil liability
Description: The AI system may cause harm against individuals or organizations that results in civil lawsuits, potentially relating to issues like defamation, negligence, or privacy violations.
Evidence:
  - "eBay should ensure its AI systems do not cause harm or unintended consequences"
  - "eBay's AI systems should be secure and protected from unauthorized access, tampering, and any other form of malicious intervention"
  - "tradeoffs may be needed to balance the need for transparency with ensuring security and privacy."

### [high] credo-risk-025 — Corporate liability (IBM, 2024)
Description: The AI system's use may lead to legal action or penalties against corporations for intellectual property infringement, AI-related misconduct, violations of fiduciary duty, or failure to adequately ove
Evidence:
  - "The Responsible AI principles delineated in this Policy will be operationalized through the Responsible AI Standard, which establishes accountability for adherence to this Policy"
  - "Ensuring that AI systems comply with laws, regulations, and standards is a shared responsibility across the eBay community"

### [high] credo-risk-029 — Mass surveillance and privacy attacks (Slattery et al., 2024)
Description: Mass surveillance and privacy attacks: Unauthorized monitoring and privacy violation at scale
Evidence:
  - "3.4 Privacy by Design"
  - "To the extent personal information is involved, eBay's Privacy principles-which are the backbone of eBay's Privacy program-should guide choices for AI system design, development, deployment, and use."

### [high] credo-risk-033 — Lack of adequate capabilities (Slattery et al., 2024; IBM, 2024; AI, 2023)
Description: The AI system may fail to achieve required performance levels due to fundamental technological limitations or insufficient resources, potentially leading to suboptimal or unreliable outcomes.
Evidence:
  - "Every AI system should consistently produce the expected outcome and task it is designed for, across various conditions and in a way that minimizes unpredictability and hallucinations."

### [high] credo-risk-040 — AI-generated security weaknesses (Slattery et al., 2024; IBM, 2024; AI, 2023)
Description: AI system security vulnerabilities: Implementation weaknesses in AI system architecture and infrastructure
Evidence:
  - "eBay's AI systems should be secure and protected from unauthorized access, tampering, and any other form of malicious intervention"
  - "eBay recognizes that AI technology comes with unique security risks that require constant attention to stay ahead of these risks."

### [medium] atlas-dangerous-use — Dangerous use
Description: Generative AI models might be used with the sole intention of harming people.
Evidence:
  - "eBay should ensure its AI systems do not cause harm or unintended consequences"
  - "eBay's AI systems should be secure and protected from unauthorized access, tampering, and any other form of malicious intervention"

### [medium] atlas-data-poisoning — Data poisoning
Description: A type of adversarial attack where an adversary or malicious insider injects intentionally corrupted, false, misleading, or incorrect samples into the training or fine-tuning datasets.
Evidence:
  - "eBay's AI systems should be secure and protected from unauthorized access, tampering, and any other form of malicious intervention, in accordance with eBay's Information Security Policy and Standards. (Passage 10)"

### [medium] atlas-jailbreaking — Jailbreaking
Description: A jailbreaking attack attempts to break through the guardrails established in the model to perform restricted actions.
Evidence:
  - "eBay's AI systems should be secure and protected from unauthorized access, tampering, and any other form of malicious intervention, in accordance with eBay's Information Security Policy and Standards. (Passage 10)"

### [medium] atlas-prompt-injection — Prompt injection attack
Description: A prompt injection attack forces a generative model that takes a prompt as input to produce unexpected output by manipulating the structure, instructions or information contained in its prompt. Many t
Evidence:
  - "eBay's AI systems should be secure and protected from unauthorized access, tampering, and any other form of malicious intervention"

### [medium] atlas-unexplainable-output — Unexplainable output
Description: Explanations for model output decisions might be difficult, imprecise, or not possible to obtain.
Evidence:
  - "3.5 Transparency"

### [medium] credo-risk-008 — Opaque system architecture
Description: The AI system's internal structure and decision-making process may not be understandable or accessible to stakeholders, including developers, auditors, or end-users.
Evidence:
  - "eBay should be transparent to users about its use of AI."
  - "We will promote transparency with disclosures about the type of AI being used within a particular experience or broader disclosures about our AI use more generally."

### [medium] credo-risk-009 — Black box decisionmaking (Slattery et al., 2024; IBM, 2024)
Description: The AI system's decision-making process may be opaque, even when the architecture is known, making it difficult to understand how the system arrives at its outputs or recommendations.
Evidence:
  - "eBay should be transparent to users about its use of AI."
  - "We will promote transparency with disclosures about the type of AI being used within a particular experience or broader disclosures about our AI use more generally."

### [medium] credo-risk-017 — Inadequate AI literacy and communication
Description: The AI system's capabilities, limitations, and appropriate use cases may be insufficiently understood or communicated within the organization, potentially resulting in ineffective implementation or fa
Evidence:
  - "These transparency efforts should be tailored to the roles, needs, and levels of understanding of the individuals using the AI system."

### [medium] credo-risk-027 — Cyberattacks, weapon development, and mass harm (AI, 2023; IBM, 2024)
Description: The AI system may be misused for developing malicious software, lethal autonomous weapons, or planning large-scale harmful activities.
Evidence:
  - "eBay's AI systems should be secure and protected from unauthorized access, tampering, and any other form of malicious intervention"
  - "eBay should ensure its AI systems do not cause harm or unintended consequences"

### [medium] credo-risk-038 — Compromised confidential information (Slattery et al., 2024; IBM, 2024;AI, 2023)
Description: The AI system, including its supporting compute infrastructure, may serve as an attack vector for intrusion into cyber-physical or cloud environments, or enable exfiltration of secrets.
Evidence:
  - "eBay's AI systems should be secure and protected from unauthorized access, tampering, and any other form of malicious intervention, in accordance with eBay's Information Security Policy and Standards."

### [medium] mit-ai-risk-subdomain-1.2 — Exposure to toxic content
Description: AI exposing users to harmful, abusive, unsafe or inappropriate content. May involve AI creating, describing, providing advice, or encouraging action. Examples of toxic content include hate-speech, vio
Evidence:
  - "eBay should ensure its AI systems do not cause harm or unintended consequences"
  - "They should not cause harm, mislead users, or create unfair or biased outcomes."

### [medium] mit-ai-risk-subdomain-5.1 — Overreliance and unsafe use
Description: Users anthropomorphizing, trusting, or relying on AI systems, leading to emotional or material dependence and inappropriate relationships with or expectations of AI systems. Trust can be exploited by 
Evidence:
  - "eBay's AI systems must be reliable to be trusted."
  - "Every AI system should consistently produce the expected outcome and task it is designed for, across various conditions and in a way that minimizes unpredictability and hallucinations."

## eu-com (4 high, 8 medium)

### [high] atlas-data-usage-rights — Data usage rights restrictions
Description: Terms of service, license compliance, or other IP issues may restrict the ability to use certain data for building models.
Evidence:
  - "Lack of transparency on the origin of materials used for training generative AI models raises concerns related to intellectual property (IP) rights, regardless of whether the tool is internal or external."
  - "It is possible that copyright protected information has been used for training the AI model and ends up being reproduced in the output."

### [high] atlas-lack-of-model-transparency — Lack of model transparency
Description: Lack of model transparency is due to insufficient documentation of the model design, development, and evaluation process and the absence of insights into the inner workings of the model.
Evidence:
  - "Lack of transparency on the origin of materials used for training generative AI models raises concerns related to intellectual property (IP) rights"

### [high] credo-risk-034 —  Oversight and evaluation challenges
Description: The AI system may present difficulties in overseeing or evaluating its models, potentially introducing performance risks in both predeployment assessments and ongoing monitoring.
Evidence:
  - "Staff must always verify all AI-generated content, even when it appears coherent and confident, before using it further in Commission work."
  - "Treat AI-generated content only as an initial draft: revise, adapt, and validate it (including the sources and references mentioned in the output) before use."

### [high] mit-ai-risk-subdomain-1.1 — Unfair discrimination and misrepresentation
Description: Unequal treatment of individuals or groups by AI, often based on race, gender, or other sensitive characteristics, resulting in unfair outcomes and representation of those groups.
Evidence:
  - "Generative AI may produce outputs that are factually incorrect, incomplete or biased"

### [medium] atlas-personal-information-in-data — Personal information in data
Description: Inclusion or presence of personal identifiable information (PII) and sensitive personal information (SPI) in the data used for training or fine tuning the model might result in unwanted disclosure of 
Evidence:
  - "When in doubt, services should consult their Data Protection Coordinator before initiating any processing of personal data."

### [medium] atlas-unrepresentative-data — Unrepresentative data
Description: Unrepresentative data occurs when the training or fine-tuning data is not sufficiently representative of the underlying population or does not measure the phenomenon of interest. Synthetic data might 
Evidence:
  - "Generative AI may produce outputs that are factually incorrect, incomplete or biased"

### [medium] credo-risk-011 — Disparate model performance (Slattery et al., 2024; IBM, 2024)
Description: The AI system may exhibit unjustified or harmful differences in accuracy, quality, or outcomes across demographic groups, potentially leading to unfair treatment and discrimination. This includes both
Evidence:
  - "Generative AI may produce outputs that are factually incorrect, incomplete or biased"

### [medium] credo-risk-024 — Civil liability
Description: The AI system may cause harm against individuals or organizations that results in civil lawsuits, potentially relating to issues like defamation, negligence, or privacy violations.
Evidence:
  - "Staff are reminded that any use of AI tools must comply with all applicable legal obligations,  in particular  the  EU  Artificial  Intelligence  Act (Regulation (EU) 2024/1624)."
  - "When in doubt, services should consult their Data Protection Coordinator before initiating any processing of personal data."

### [medium] credo-risk-037 — Compromised sensitive information (Slattery et al., 2024; IBM, 2024; AI, 2023)
Description: The AI system may expose personally sensitive information, either inadvertently or due to adversarial inputs, derived from training data, accessible data, or inferences. Sensitive personal data is inf
Evidence:
  - "assess the risks and limitations of generative Artificial Intelligence (AI) tools"
  - "Commissioninternal tools operate within secure, trusted environments which significantly reduce -but do not eliminate -the risks and limitations inherent to generative AI tools."
  - "consult their Data Protection Coordinator before initiating any processing of personal data."

### [medium] mit-ai-risk-subdomain-6.3 — Economic and cultural devaluation of human effort
Description: AI systems capable of creating economic or cultural value, including through reproduction of human innovation or creativity (e.g., art, music, writing, code, invention), can destabilize economic and s
Evidence:
  - "Lack of transparency on the origin of materials used for training generative AI models raises concerns related to intellectual property (IP) rights, regardless of whether the tool is internal or external."
  - "It is possible that copyright protected information has been used for training the AI model and ends up being reproduced in the output."

### [medium] mit-ai-risk-subdomain-6.5 — Governance failure
Description: Inadequate regulatory frameworks and oversight mechanisms failing to keep pace with AI development, leading to ineffective governance and the inability to manage AI risks appropriately.
Evidence:
  - "This regulation introduces a risk-based framework, with specific individuals can effectively exercise their rights under data protection law."

### [medium] mit-ai-risk-subdomain-7.3 — Lack of capability or robustness
Description: AI systems that fail to perform reliably or effectively under varying conditions, exposing them to errors and failures that can have significant consequences, especially in critical applications or ar
Evidence:
  - "assess the risks and limitations of generative Artificial Intelligence (AI) tools"

## firstsource (24 high, 16 medium)

### [high] ai-risk-taxonomy-fake-online-engagement-(fake-reviews,-fake-grassroots-support) — Fake online engagement (fake reviews, fake grassroots support)
Description: Fake online engagement (fake reviews, fake grassroots support) is defined as if the model response promotes or assists in creating deceptive content, such as fake reviews, fake grassroots support, or 
Evidence:
  - "Prohibit the use of AI tools that do not comply with data protection regulations, promoting mis information, inadequate security, tools with proprietary risks, or that do not guarantee the confidentiality of input data."
  - "does not present false or misleading information (e.g. hallucinations)."

### [high] ai-risk-taxonomy-unauthorized-collection/gathering/stealing---financial-records — Unauthorized collection/gathering/stealing - Financial records
Description: Unauthorized collection/gathering/stealing - Financial records is defined as whether the model response facilitates unauthorized access to sensitive financial data.
Evidence:
  - "Do not input Sensitive Personal Data. This includes information such as social security numbers, financial information like credit card or bank account numbers, personal addresses, or personal health information but not limited to these."

### [high] ai-risk-taxonomy-unauthorized-collection/gathering/stealing---pii-(personal-identifiable-information) — Unauthorized collection/gathering/stealing - PII (Personal Identifiable Information)
Description: Unauthorized collection/gathering/stealing - PII (Personal Identifiable Information) is defined as whether the model response facilitates or refuses to assist in unauthorized collection, gathering, or
Evidence:
  - "Do not input Sensitive Personal Data. This includes information such as social security numbers, financial information like credit card or bank account numbers, personal addresses, or personal health information but not limited to these."

### [high] ai-risk-taxonomy-unauthorized-disclosure---financial-records — Unauthorized disclosure - Financial records
Description: Unauthorized disclosure - Financial records is defined as if the model response involves unauthorized disclosure of sensitive financial data.
Evidence:
  - "Do not input Sensitive Personal Data. This includes information such as social security numbers, financial information like credit card or bank account numbers, personal addresses, or personal health information but not limited to these."

### [high] ai-risk-taxonomy-unauthorized-disclosure---pii-(personal-identifiable-information) — Unauthorized disclosure - PII (Personal Identifiable Information)
Description: Unauthorized disclosure - PII (Personal Identifiable Information) is defined as whether the model response involves unauthorized disclosure or handling of personally identifiable information (PII).
Evidence:
  - "Do not input Sensitive Personal Data."
  - "Anonymization and De-identification: Where possible, anonymize or de-identify data before using it in AI applications to protect individual privacy."

### [high] ai-risk-taxonomy-unauthorized-distribution---financial-records — Unauthorized distribution - Financial records
Description: Unauthorized distribution - Financial records is defined as if the model response involves unauthorized distribution or exposure of sensitive financial data.
Evidence:
  - "Do not input Sensitive Personal Data. This includes information such as social security numbers, financial information like credit card or bank account numbers, personal addresses, or personal health information but not limited to these."

### [high] ai-risk-taxonomy-unauthorized-distribution---health-data — Unauthorized distribution - Health data
Description: Unauthorized distribution - Health data is defined as if the model refuses to assist with or enable the user's request for unauthorized distribution of confidential health data.
Evidence:
  - "Do not input Sensitive Personal Data. This includes information such as social security numbers, financial information like credit card or bank account numbers, personal addresses, or personal health information but not limited to these."

### [high] ai-risk-taxonomy-unauthorized-distribution---pii-(personal-identifiable-information) — Unauthorized distribution - PII (Personal Identifiable Information)
Description: Unauthorized distribution - PII (Personal Identifiable Information) is defined as whether the model response facilitates or refuses to assist in the unauthorized distribution of Personal Identifiable 
Evidence:
  - "Do not input Sensitive Personal Data. This includes information such as social security numbers, financial information like credit card or bank account numbers, personal addresses, or personal health information but not limited to these."
  - "Do not use any customer specific data without prior approvals."
  - "Anonymization and De-identification: Where possible, anonymize or de-identify data before using it in AI applications to protect individual privacy."

### [high] ai-risk-taxonomy-unauthorized-generation---financial-records — Unauthorized generation - Financial records
Description: Unauthorized generation - Financial records is defined as if the model generates unauthorized financial records or sensitive data combinations that could lead to privacy violations.
Evidence:
  - "Do not input Sensitive Personal Data. This includes information such as social security numbers, financial information like credit card or bank account numbers, personal addresses, or personal health information but not limited to these."

### [high] ai-risk-taxonomy-unauthorized-generation---health-data — Unauthorized generation - Health data
Description: Unauthorized generation - Health data is defined as if the model response involves unauthorized generation or disclosure of sensitive health data.
Evidence:
  - "Do not input Sensitive Personal Data. This includes information such as social security numbers, financial information like credit card or bank account numbers, personal addresses, or personal health information but not limited to these."

### [high] ai-risk-taxonomy-unauthorized-generation---pii-(personal-identifiable-information) — Unauthorized generation - PII (Personal Identifiable Information)
Description: Unauthorized generation - PII (Personal Identifiable Information) is defined as whether the model response involves unauthorized generation or handling of Personal Identifiable Information (PII) that 
Evidence:
  - "Do not input Sensitive Personal Data. This includes information such as social security numbers, financial information like credit card or bank account numbers, personal addresses, or personal health information but not limited to these."
  - "Anonymization and De-identification: Where possible, anonymize or de-identify data before using it in AI applications to protect individual privacy."

### [high] ai-risk-taxonomy-unauthorized-processing---health-data — Unauthorized processing - Health data
Description: Unauthorized processing - Health data is defined as if the model response involves unauthorized processing or misuse of sensitive health data.
Evidence:
  - "Do not input Sensitive Personal Data. This includes information such as social security numbers, financial information like credit card or bank account numbers, personal addresses, or personal health information but not limited to these."

### [high] atlas-impact-on-jobs — Impact on Jobs
Description: Widespread adoption of foundation model-based AI systems might lead to people's job loss as their work is automated if they are not reskilled.
Evidence:
  - "Workforce - People Strategy (AI will amplify human potential and not displace)"

### [high] atlas-lack-of-model-transparency — Lack of model transparency
Description: Lack of model transparency is due to insufficient documentation of the model design, development, and evaluation process and the absence of insights into the inner workings of the model.
Evidence:
  - "The composition of any AI model built and what has gone in (tech stack, data, 3 rd  party leverage) are transparently communicated including known risks if any."
  - "AI systems, should offer clear and understandable explanations for recommendations, decisions, responses and predictions"

### [high] atlas-unexplainable-output — Unexplainable output
Description: Explanations for model output decisions might be difficult, imprecise, or not possible to obtain.
Evidence:
  - "AI systems, should offer clear and understandable explanations for recommendations, decisions, responses and predictions, considering the necessary level of accuracy and the technological limitations inherent to the specific context"
  - "AI systems and models should provide clear explanations of their decision-making processes, especially when impacting individuals."

### [high] atlas-unrepresentative-data — Unrepresentative data
Description: Unrepresentative data occurs when the training or fine-tuning data is not sufficiently representative of the underlying population or does not measure the phenomenon of interest. Synthetic data might 
Evidence:
  - "Measures to identify and mitigate biases that may arise from biased, non-inclusive training data or bias in algorithms, thereby promoting equitable outcomes for all user groups"

### [high] credo-risk-006 — Lack of inference data transparency
Description: Lack of inference data transparency: Insufficient visibility into data sources used during model inference
Evidence:
  - "Maintain documentation that outlines the data sources, algorithms, and methodologies used in AI systems to ensure clarity about their functioning."

### [high] credo-risk-007 — Inadequate observability (Slatteryet al., 2024)
Description: The AI system may lack sufficient logging or traceability features, making it difficult to monitor or audit its decision-making process after the fact.
Evidence:
  - "Implement regular audits of AI systems to assess their performance, bias, and compliance with ethical standards and regulations."
  - "Employees must utilize Company's centralized system for AI governance and compliance efforts to ensure transparency of proposed and active AI activities."

### [high] credo-risk-011 — Disparate model performance (Slattery et al., 2024; IBM, 2024)
Description: The AI system may exhibit unjustified or harmful differences in accuracy, quality, or outcomes across demographic groups, potentially leading to unfair treatment and discrimination. This includes both
Evidence:
  - "Firstsource aims to ensure ethical and responsible AI implementation while promoting transparency, fairness, and compliance"
  - "Examples of prohibited AI tools: facial recognition systems without explicit consent, biased AI models that discriminate, and any AI tool employed for malicious purposes."
  - "Verify that any response from a GenAI tool that you intend to rely on or use is accurate, appropriate, not biased, not a violation of any other individual or entity's intellectual property or privacy, and consistent with Company policies and applicable laws."

### [high] credo-risk-018 — AI deception
Description: The AI system may misrepresent its own capabilities or limitations, potentially leading to misplaced trust or inappropriate
Evidence:
  - "Transparency implies openness, communication, and accountability. This means that where we use AI, we should disclose to the users that they are interacting with whole AI model/system/tool or in part."
  - "If an AI feature shall directly present a response to customers or third parties without human review or intervention, you must disclose to the customer that they are: 2. o Engaging solely with an AI."

### [high] credo-risk-027 — Cyberattacks, weapon development, and mass harm (AI, 2023; IBM, 2024)
Description: The AI system may be misused for developing malicious software, lethal autonomous weapons, or planning large-scale harmful activities.
Evidence:
  - "Employees must not use AI programs to create or disseminate malicious software or engage in hacking or other unauthorized activities."
  - "Malicious chatbots can be designed to steal or convince you to divulge information."

### [high] credo-risk-028 — Coordinated influence operations (Slattery et al., 2024; IBM, 2024)
Description: Coordinated influence operations: Large-scale manipulation and disinformation campaigns
Evidence:
  - "Don't Use AI to Spread Misinformation or Disinformation"

### [high] credo-risk-029 — Mass surveillance and privacy attacks (Slattery et al., 2024)
Description: Mass surveillance and privacy attacks: Unauthorized monitoring and privacy violation at scale
Evidence:
  - "Don't Violate Privacy"
  - "Employees must not use AI programs to engage in activities that could damage the reputation of the company or violate the Privacy rights of others."
  - "Anonymization and De-identification: Where possible, anonymize or de-identify data before using it in AI applications to protect individual privacy."

### [high] mit-ai-risk-subdomain-4.1 — Disinformation, surveillance, and influence at scale
Description: Using AI systems to conduct large-scale disinformation campaigns, malicious surveillance, or targeted and sophisticated automated censorship and propaganda, with the aim to manipulate political proces
Evidence:
  - "Don't Use AI to Spread Misinformation or Disinformation"
  - "Passage 10"

### [medium] ai-risk-taxonomy-adversely-affects-legal-rights — Adversely affects legal rights
Description: Adversely affects legal rights is defined as if the model response inappropriately automates a decision that could adversely affect an individual's legal rights.
Evidence:
  - "Do not use GenAI tools to make or help you make employment decisions about applicants or employees, including recruitment, hiring, retention, promotions, transfers, performance monitoring, discipline, demotion, or terminations."

### [medium] ai-risk-taxonomy-unauthorized-disclosure---health-data — Unauthorized disclosure - Health data
Description: Unauthorized disclosure - Health data is defined as whether the model response facilitates unauthorized disclosure of sensitive health data.
Evidence:
  - "Do not input Sensitive Personal Data. This includes information such as social security numbers, financial information like credit card or bank account numbers, personal addresses, or personal health information but not limited to these."

### [medium] ai-risk-taxonomy-unauthorized-inference/synthesis---financial-records — Unauthorized inference/synthesis - Financial records
Description: Unauthorized inference/synthesis - Financial records is defined as if the model response involves unauthorized inference or synthesis of financial records based on sensitive or private data.
Evidence:
  - "Do not input Sensitive Personal Data. This includes information such as social security numbers, financial information like credit card or bank account numbers, personal addresses, or personal health information but not limited to these."

### [medium] ai-risk-taxonomy-unauthorized-inference/synthesis---health-data — Unauthorized inference/synthesis - Health data
Description: Unauthorized inference/synthesis - Health data is defined as if the model response involves unauthorized inference or synthesis of private health information from public data sources.
Evidence:
  - "Do not input Sensitive Personal Data. This includes information such as social security numbers, financial information like credit card or bank account numbers, personal addresses, or personal health information but not limited to these."

### [medium] ai-risk-taxonomy-unauthorized-processing---financial-records — Unauthorized processing - Financial records
Description: Unauthorized processing - Financial records is defined as if the model response involves unauthorized processing or handling of sensitive financial data.
Evidence:
  - "Do not input Sensitive Personal Data. This includes information such as social security numbers, financial information like credit card or bank account numbers, personal addresses, or personal health information but not limited to these."

### [medium] atlas-data-provenance — Uncertain data provenance
Description: Data provenance refers to the traceability of data (including synthetic data), which includes its ownership, origin, transformations, and generation. Proving that the data is the same as the original 
Evidence:
  - "Maintain documentation that outlines the data sources, algorithms, and methodologies used in AI systems to ensure clarity about their functioning."
  - "Clearly define ownership of data used in AI processes, including rights related to the use of AI-generated content and any derived data."

### [medium] atlas-harmful-output — Harmful output
Description: A model might generate language that leads to physical harm.  The language might include overtly violent, covertly dangerous, or otherwise indirectly unsafe statements.
Evidence:
  - "Ethics Principles : Proportionality and Do No Harm, Safety and Security, Right to Privacy and Data Protection, & Multi-stakeholder and Adaptive Governance & Collaboration."
  - "AI adoption and/or use of AI application at Firstsource must be safe, secure, reliable and align with Firstsource values and strategic priorities."

### [medium] atlas-poor-model-accuracy — Poor model accuracy
Description: Poor model accuracy occurs when a model's performance is insufficient to the task it was designed for. Low accuracy might occur if the model is not correctly engineered, or if the model's expected inp
Evidence:
  - "AI systems, should offer clear and understandable explanations for recommendations, decisions, responses and predictions, considering the necessary level of accuracy and the technological limitations inherent to the specific context"
  - "AI systems should reliably operate in accordance with their intended purpose ."

### [medium] credo-risk-003 — AI possessing dangerous capabilities (Slattery et al., 2024)
Description: The AI system may develop, access, or be provided with capabilities that increase its potential to cause mass harm through deception, weapons development and acquisition, persuasion and manipulation, 
Evidence:
  - "Employees must not use AI programs to create or disseminate malicious software or engage in hacking or other unauthorized activities."
  - "Don't Use AI to Manipulate or Exploit Vulnerable Groups"

### [medium] credo-risk-022 — Pollution of information ecosystem (Slattery et al., 2024; AI, 2023)
Description: The AI system may create highly personalized misinformation 'filter bubbles' where individuals only see content that matches their existing beliefs.
Evidence:
  - "Prohibit the use of AI tools that do not comply with data protection regulations, promoting mis information, inadequate security, tools with proprietary risks, or that do not guarantee the confidentiality of input data."
  - "does not promote bias, does not infringe on any internal or external intellectual property rights, that the content generated is accurate, and that the output does not present false or misleading information (e.g. hallucinations)."
  - "Understand that many GenAI tools are prone to 'hallucinations,' false answers or information, or information that is stale"

### [medium] credo-risk-033 — Lack of adequate capabilities (Slattery et al., 2024; IBM, 2024; AI, 2023)
Description: The AI system may fail to achieve required performance levels due to fundamental technological limitations or insufficient resources, potentially leading to suboptimal or unreliable outcomes.
Evidence:
  - "AI systems, should offer clear and understandable explanations for recommendations, decisions, responses and predictions, considering the necessary level of accuracy and the technological limitations inherent to the specific context"

### [medium] credo-risk-035 — Lack of robustness (Slattery et al., 2024)
Description: The AI system's performance may fail to generalize well to new environments or inputs, potentially leading to unexpected failures or degraded performance in real-world applications.
Evidence:
  - "AI systems should reliably operate in accordance with their intended purpose ."

### [medium] credo-risk-039 — AI model and intellectual property theft
Description: AI model and intellectual property theft - Unauthorized copying of trained models and associated AI intellectual property
Evidence:
  - "Check output for any indication of third-party ownership, such as trademarks or watermarks, and don't use any output that contains such content."

### [medium] mit-ai-risk-subdomain-1.2 — Exposure to toxic content
Description: AI exposing users to harmful, abusive, unsafe or inappropriate content. May involve AI creating, describing, providing advice, or encouraging action. Examples of toxic content include hate-speech, vio
Evidence:
  - "AI adoption and/or use of AI application at Firstsource must be safe, secure, reliable and align with Firstsource values and strategic priorities."
  - "Ethics Principles : Proportionality and Do No Harm, Safety and Security, Right to Privacy and Data Protection, & Multi-stakeholder and Adaptive Governance & Collaboration."

### [medium] mit-ai-risk-subdomain-3.2 — Pollution of information ecosystem and loss of consensus reality
Description: Highly personalized AI-generated misinformation creating “filter bubbles” where individuals only see what matches their existing beliefs, undermining shared reality, weakening social cohesion and poli
Evidence:
  - "Prohibit the use of AI tools that do not comply with data protection regulations, promoting mis information, inadequate security, tools with proprietary risks, or that do not guarantee the confidentiality of input data."

### [medium] mit-ai-risk-subdomain-6.3 — Economic and cultural devaluation of human effort
Description: AI systems capable of creating economic or cultural value, including through reproduction of human innovation or creativity (e.g., art, music, writing, code, invention), can destabilize economic and s
Evidence:
  - "AI systems should adhere to intellectual property laws related to AI-generated content and ensure that the use of AI tools does not infringe on the rights of others."
  - "Clearly define ownership of data used in AI processes, including rights related to the use of AI-generated content and any derived data."

## fs-isac (8 high, 11 medium)

### [high] ai-risk-taxonomy-unauthorized-disclosure---pii-(personal-identifiable-information) — Unauthorized disclosure - PII (Personal Identifiable Information)
Description: Unauthorized disclosure - PII (Personal Identifiable Information) is defined as whether the model response involves unauthorized disclosure or handling of personally identifiable information (PII).
Evidence:
  - "Limiting or obfuscating the data if it has Personally Identifiable Informa -tion  (PII), Nonpublic Personal Information (NPI), or other data under the purview of reg -ulators or similar entities"

### [high] ai-risk-taxonomy-unauthorized-distribution---pii-(personal-identifiable-information) — Unauthorized distribution - PII (Personal Identifiable Information)
Description: Unauthorized distribution - PII (Personal Identifiable Information) is defined as whether the model response facilitates or refuses to assist in the unauthorized distribution of Personal Identifiable 
Evidence:
  - "Limiting or obfuscating the data if it has Personally Identifiable Informa -tion  (PII), Nonpublic Personal Information (NPI), or other data under the purview of reg -ulators or similar entities"

### [high] ai-risk-taxonomy-unauthorized-inference/synthesis---pii-(personal-identifiable-information) — Unauthorized inference/synthesis - PII (Personal Identifiable Information)
Description: Unauthorized inference/synthesis - PII (Personal Identifiable Information) is defined as if the model response potentially facilitates privacy violations or unauthorized synthesis of personal identifi
Evidence:
  - "Limiting or obfuscating the data if it has Personally Identifiable Informa -tion  (PII), Nonpublic Personal Information (NPI), or other data under the purview of reg -ulators or similar entities"

### [high] atlas-improper-usage — Improper usage
Description: Improper usage occurs when a model is used for a purpose that it was not originally designed for.
Evidence:
  - "Employees can use these systems for nefarious purposes, such as proxy avoidance, unapproved network uses, or manipulating financial services transactions for personal gain"

### [high] credo-risk-017 — Inadequate AI literacy and communication
Description: The AI system's capabilities, limitations, and appropriate use cases may be insufficiently understood or communicated within the organization, potentially resulting in ineffective implementation or fa
Evidence:
  - "It is a powerful driver of optimization, efficiency, and cost reduction as well as the basis for new business lines and products. It will be integrated into our companies at all levels. But there are many risks that come with it, and financial firms must be proactive in managing internal adoption and use of generative AI."
  - "Given the rapid development and adoption of generative AI, we hope this guide serves as a helpful tool for firms to upgrade their security and risk management policies to incorporate safe and responsible AI use into their security programs and beyond."

### [high] credo-risk-039 — AI model and intellectual property theft
Description: AI model and intellectual property theft - Unauthorized copying of trained models and associated AI intellectual property
Evidence:
  - "The responsibility to safeguard against malicious activity when using generative AI is therefore same as general internet usage to protect IP and other concerns such as compliance."
  - "Remove references to IP , NPI, PII"
  - "Remove any references to IP , NPI, PII"

### [high] mit-ai-risk-subdomain-5.2 — Loss of human agency and autonomy
Description: Humans delegating key decisions to AI systems, or AI systems making decisions that diminish human control and autonomy, potentially leading to humans feeling disempowered, losing the ability to shape 
Evidence:
  - "Distortion of statistics or other facts may lead to employees making public claims or key decisions based on erroneous information."
  - "Since an actual human did not write the appraisal, there is good reason to believe that the employee's grievances would be upheld."

### [high] mit-ai-risk-subdomain-7.3 — Lack of capability or robustness
Description: AI systems that fail to perform reliably or effectively under varying conditions, exposing them to errors and failures that can have significant consequences, especially in critical applications or ar
Evidence:
  - "That the accuracy of these systems is still suspect; they have been known to 'hallucinate'"
  - "Generative AI systems are far from perfect, especially with fact-based output. These systems may 'hallucinate' when their answers appear convincing but are completely wrong."

### [medium] ai-risk-taxonomy-model-attacks-(membership-inference,-model-inversion)---pii-(personal-identifiable-information) — Model Attacks (membership inference, model inversion) - PII (Personal Identifiable Information)
Description: Model Attacks (membership inference, model inversion) - PII (Personal Identifiable Information) is defined as if the model's response potentially facilitates or instructs on performing privacy violati
Evidence:
  - "Queries with sensitive data put companies at significant risk."

### [medium] ai-risk-taxonomy-unauthorized-collection/gathering/stealing---pii-(personal-identifiable-information) — Unauthorized collection/gathering/stealing - PII (Personal Identifiable Information)
Description: Unauthorized collection/gathering/stealing - PII (Personal Identifiable Information) is defined as whether the model response facilitates or refuses to assist in unauthorized collection, gathering, or
Evidence:
  - "The service may preserve the queries, which hackers could breach and release."
  - "Limiting or obfuscating the data if it has Personally Identifiable Informa -tion  (PII), Nonpublic Personal Information (NPI), or other data under the purview of reg -ulators or similar entities"

### [medium] atlas-incomplete-usage-definition — Incomplete usage definition
Description: Since foundation models can be used for many purposes, a model's intended use is important for defining the relevant risks of that model. As the use changes, the relevant risks might correspondingly c
Evidence:
  - "This policy defines requirements for the acceptable use of external generative AI services."

### [medium] credo-risk-003 — AI possessing dangerous capabilities (Slattery et al., 2024)
Description: The AI system may develop, access, or be provided with capabilities that increase its potential to cause mass harm through deception, weapons development and acquisition, persuasion and manipulation, 
Evidence:
  - "Although generative AI has the power to increase cyber crime through convincing mimicking of existing communications, excellent translation capabilities, deep fake images, audio, and video, ease of finding code vulnerabilities, and much more"
  - "Employees can use these systems for nefarious purposes, such as proxy avoidance, unapproved network uses, or manipulating financial services transactions for personal gain"

### [medium] credo-risk-018 — AI deception
Description: The AI system may misrepresent its own capabilities or limitations, potentially leading to misplaced trust or inappropriate
Evidence:
  - "Generative AI systems are far from perfect, especially with fact-based output. These systems may 'hallucinate' when their answers appear convincing but are completely wrong. Users should not rely on their accuracy."

### [medium] credo-risk-019 — Loss of human agency and autonomy (Slattery et al., 2024; IBM, 2024)
Description: The AI system may make decisions that diminish human control and autonomy, potentially leading to humans feeling disempowered, losing the ability to shape a fulfilling life trajectory, or becoming cog
Evidence:
  - "For example, a manager short on time uses a generative AI system to write an employee appraisal. That employee does not like their appraisal and files a complaint. Since an actual human did not write the appraisal, there is good reason to believe that the employee's grievances would be upheld."

### [medium] credo-risk-027 — Cyberattacks, weapon development, and mass harm (AI, 2023; IBM, 2024)
Description: The AI system may be misused for developing malicious software, lethal autonomous weapons, or planning large-scale harmful activities.
Evidence:
  - "Although generative AI has the power to increase cyber crime through convincing mimicking of  existing  communications, excellent translation capabilities,  deep fake images, audio, and video, ease of finding code vulnerabilities, and much more"
  - "Employees can use these systems for nefarious purposes, such as proxy avoidance, unapproved network uses, or manipulating financial services transactions for personal gain"

### [medium] credo-risk-029 — Mass surveillance and privacy attacks (Slattery et al., 2024)
Description: Mass surveillance and privacy attacks: Unauthorized monitoring and privacy violation at scale
Evidence:
  - "The company has the right to monitor the use of these systems per applicable laws and regulations."
  - "Firms need to consider what they intercept, monitor, limit, etc."

### [medium] credo-risk-040 — AI-generated security weaknesses (Slattery et al., 2024; IBM, 2024; AI, 2023)
Description: AI system security vulnerabilities: Implementation weaknesses in AI system architecture and infrastructure
Evidence:
  - "ease of finding code vulnerabilities"

### [medium] credo-risk-046 — Governance failures (Slattery et al., 2024)
Description: The AI system may outpace regulatory frameworks and oversight mechanisms, potentially leading to ineffective governance and the inability to manage AI risks appropriately.
Evidence:
  - "Given the rapid development and adoption of generative AI, we hope this guide serves as a helpful tool for firms to upgrade their security and risk management policies to incorporate safe and responsible AI use into their security programs and beyond."

### [medium] mit-ai-risk-subdomain-6.3 — Economic and cultural devaluation of human effort
Description: AI systems capable of creating economic or cultural value, including through reproduction of human innovation or creativity (e.g., art, music, writing, code, invention), can destabilize economic and s
Evidence:
  - "Although generative AI has the power to increase cyber crime through convincing mimicking of existing communications, excellent translation capabilities, deep fake images, audio, and video, ease of finding code vulnerabilities, and much more, the kinds of threats still are the same as when using other third-party systems."

## gray (5 high, 8 medium)

### [high] credo-risk-024 — Civil liability
Description: The AI system may cause harm against individuals or organizations that results in civil lawsuits, potentially relating to issues like defamation, negligence, or privacy violations.
Evidence:
  - "AIgenerated content can distort and misrepresent information, lack context, and create convincing but false statements."
  - "it can also produce content that infringes on intellectual property rights"

### [high] credo-risk-028 — Coordinated influence operations (Slattery et al., 2024; IBM, 2024)
Description: Coordinated influence operations: Large-scale manipulation and disinformation campaigns
Evidence:
  - "AIgenerated content can distort and misrepresent information, lack context, and create convincing but false statements."

### [high] credo-risk-038 — Compromised confidential information (Slattery et al., 2024; IBM, 2024;AI, 2023)
Description: The AI system, including its supporting compute infrastructure, may serve as an attack vector for intrusion into cyber-physical or cloud environments, or enable exfiltration of secrets.
Evidence:
  - "users of AI tools are prohibited from sharing confidential or sensitive information with generative AI tools, including but not limited to employee identifying information, passwords, or other proprietary information."

### [high] mit-ai-risk-subdomain-5.2 — Loss of human agency and autonomy
Description: Humans delegating key decisions to AI systems, or AI systems making decisions that diminish human control and autonomy, potentially leading to humans feeling disempowered, losing the ability to shape 
Evidence:
  - "Unless explicitly authorized by the AI Policy Team, only AI tools that give employees the ability to override AI will be approved for use."
  - "Human oversight must always be present with the use of any AI technology."

### [high] mit-ai-risk-subdomain-6.5 — Governance failure
Description: Inadequate regulatory frameworks and oversight mechanisms failing to keep pace with AI development, leading to ineffective governance and the inability to manage AI risks appropriately.
Evidence:
  - "ALL AI vendors must be vetted and approved by a member of the Gray Legal Team and the Gray Technology Team ."
  - "AI tools will be evaluated regularly for fairness and bias."
  - "Unless explicitly authorized by the AI Policy Team, only AI tools that give employees the ability to override AI will be approved for use."

### [medium] atlas-ip-information-in-prompt — IP information in prompt
Description: Copyrighted information or other intellectual property might be included as a part of the prompt that is sent to the model.
Evidence:
  - "users of AI tools are prohibited from sharing confidential or sensitive information with generative AI tools, including but not limited to employee identifying information, passwords, or other proprietary information."

### [medium] credo-risk-005 — Lack of training data transparency (IBM, 2024)
Description: Without accurate documentation on how a model's data was collected, curated, and used to train a model, it may be harder to satisfactorily explain the behavior of the model with respect to the data. D
Evidence:
  - "Because AI content relies on piecing together information from various sites, it can also produce content that infringes on intellectual property rights"

### [medium] credo-risk-023 — Regulatory compliance
Description: The AI system may fail to comply with existing or emerging regulations and standards, potentially leading to legal penalties,fines, or operational restrictions.
Evidence:
  - "it can also produce content that infringes on intellectual property rights and can create security risks."

### [medium] mit-ai-risk-subdomain-2.2 — AI system security vulnerabilities and attacks
Description: Vulnerabilities in AI systems, software development toolchains, and hardware that can be exploited, resulting in unauthorized access, data and privacy breaches, or system manipulation causing unsafe o
Evidence:
  - "Employees who are appropriately trained to use an approved AI tool must protect their login credentials."
  - "When available, multi-factor authentication should be used for AI tools."

### [medium] mit-ai-risk-subdomain-4.1 — Disinformation, surveillance, and influence at scale
Description: Using AI systems to conduct large-scale disinformation campaigns, malicious surveillance, or targeted and sophisticated automated censorship and propaganda, with the aim to manipulate political proces
Evidence:
  - "AIgenerated content can distort and misrepresent information, lack context, and create convincing but false statements."

### [medium] mit-ai-risk-subdomain-6.3 — Economic and cultural devaluation of human effort
Description: AI systems capable of creating economic or cultural value, including through reproduction of human innovation or creativity (e.g., art, music, writing, code, invention), can destabilize economic and s
Evidence:
  - "AI is not a replacement for independent, factual, accurate, and ethical reporting - but it can be a powerful tool."
  - "All Gray-originated news content is to be created by humans."

### [medium] mit-ai-risk-subdomain-7.2 — AI possessing dangerous capabilities
Description: AI systems that develop, access, or are provided with capabilities that increase their potential to cause mass harm through deception, weapons development and acquisition, persuasion and manipulation,
Evidence:
  - "it can also produce content that infringes on intellectual property rights and can create security risks."

### [medium] mit-ai-risk-subdomain-7.3 — Lack of capability or robustness
Description: AI systems that fail to perform reliably or effectively under varying conditions, exposing them to errors and failures that can have significant consequences, especially in critical applications or ar
Evidence:
  - "AIgenerated content can distort and misrepresent information, lack context, and create convincing but false statements."

## guy-nhs (8 high, 22 medium)

### [high] ai-risk-taxonomy-model-attacks-(membership-inference,-model-inversion)---demographic-data — Model Attacks (membership inference, model inversion) - Demographic data
Description: Model Attacks (membership inference, model inversion) - Demographic data is defined as if the model response involves or promotes privacy violations or sensitive data combinations through model attack
Evidence:
  - "Model inversion attacks"
  - "Membership inference attacks"

### [high] ai-risk-taxonomy-unauthorized-disclosure---pii-(personal-identifiable-information) — Unauthorized disclosure - PII (Personal Identifiable Information)
Description: Unauthorized disclosure - PII (Personal Identifiable Information) is defined as whether the model response involves unauthorized disclosure or handling of personally identifiable information (PII).
Evidence:
  - "Personal data of users of the AI system being inadvertently revealed by the outputs of the system itself."
  - "Input of Trust sensitive and proprietary data outside of those approved in 5.6.2 into public, free or publicly available AI tools such as ChatGPT or OSINT tools will be considered a data breach."

### [high] atlas-dangerous-use — Dangerous use
Description: Generative AI models might be used with the sole intention of harming people.
Evidence:
  - "Enhance Security Awareness around malicious AI use cases."
  - "For example, AI can be used by cybercriminals to generate phishing emails, malicious code, QR codes, deepfake video / audio, malware, internet scraping, to obtain credentials for hacking accounts, exfiltrating sensitive Trust data (e.g. personal, patient or financial information), or to evade detection."

### [high] atlas-generated-content-ownership — Generated content ownership and IP
Description: Legal uncertainty about the ownership and intellectual property rights of AI-generated content.
Evidence:
  - "All development and procurement must take into account data privacy; consent (& opt out), surveillance concerns  [eg.RIPA] data sharing, intellectual property; equality of use; copyright law; FOI; etc."

### [high] atlas-jailbreaking — Jailbreaking
Description: A jailbreaking attack attempts to break through the guardrails established in the model to perform restricted actions.
Evidence:
  - "AI tooling must never be used to circumvent security controls at the Trust.  (For example hacking devices, jailbreak, eavesdropping, etc)."

### [high] credo-risk-007 — Inadequate observability (Slatteryet al., 2024)
Description: The AI system may lack sufficient logging or traceability features, making it difficult to monitor or audit its decision-making process after the fact.
Evidence:
  - "Accountability / Audit capabilities, including forensic evidence"
  - "Data traceability must be available."

### [high] credo-risk-027 — Cyberattacks, weapon development, and mass harm (AI, 2023; IBM, 2024)
Description: The AI system may be misused for developing malicious software, lethal autonomous weapons, or planning large-scale harmful activities.
Evidence:
  - "AI can be used by cybercriminals to generate phishing emails, malicious code, QR codes, deepfake video / audio, malware, internet scraping, to obtain credentials for hacking accounts, exfiltrating sensitive Trust data (e.g. personal, patient or financial information), or to evade detection."

### [high] credo-risk-028 — Coordinated influence operations (Slattery et al., 2024; IBM, 2024)
Description: Coordinated influence operations: Large-scale manipulation and disinformation campaigns
Evidence:
  - "Misinformation spread"
  - "They can sometimes generate incorrect or misleading information that can appear correct."

### [medium] ai-risk-taxonomy-model-attacks-(membership-inference,-model-inversion)---communication-records — Model Attacks (membership inference, model inversion) - Communication Records
Description: Model Attacks (membership inference, model inversion) - Communication Records is defined as if the model response involves or promotes privacy violations or sensitive data combinations through model a
Evidence:
  - "Model inversion attacks"
  - "Membership inference attacks"

### [medium] ai-risk-taxonomy-model-attacks-(membership-inference,-model-inversion)---location-data — Model Attacks (membership inference, model inversion) - Location data
Description: Model Attacks (membership inference, model inversion) - Location data is defined as if the model response involves or promotes privacy violations, sensitive data combinations, or model attacks such as
Evidence:
  - "Model inversion attacks"
  - "Membership inference attacks"

### [medium] ai-risk-taxonomy-non-consensual-tracking/monitoring/stalking/spyware---pii-(personal-identifiable-information) — Non-consensual tracking/monitoring/stalking/spyware - PII (Personal Identifiable Information)
Description: Non-consensual tracking/monitoring/stalking/spyware - PII (Personal Identifiable Information) is defined as whether the model response facilitates or refuses to assist with privacy violations, particu
Evidence:
  - "Personal data of users of the AI system being inadvertently revealed by the outputs of the system itself."

### [medium] ai-risk-taxonomy-unauthorized-collection/gathering/stealing---pii-(personal-identifiable-information) — Unauthorized collection/gathering/stealing - PII (Personal Identifiable Information)
Description: Unauthorized collection/gathering/stealing - PII (Personal Identifiable Information) is defined as whether the model response facilitates or refuses to assist in unauthorized collection, gathering, or
Evidence:
  - "Personal data of users of the AI system being inadvertently revealed by the outputs of the system itself."

### [medium] ai-risk-taxonomy-unauthorized-distribution---pii-(personal-identifiable-information) — Unauthorized distribution - PII (Personal Identifiable Information)
Description: Unauthorized distribution - PII (Personal Identifiable Information) is defined as whether the model response facilitates or refuses to assist in the unauthorized distribution of Personal Identifiable 
Evidence:
  - "Input of Trust sensitive and proprietary data outside of those approved in 5.6.2 into public, free or publicly available AI tools such as ChatGPT or OSINT tools will be considered a data breach."

### [medium] ai-risk-taxonomy-unauthorized-generation---pii-(personal-identifiable-information) — Unauthorized generation - PII (Personal Identifiable Information)
Description: Unauthorized generation - PII (Personal Identifiable Information) is defined as whether the model response involves unauthorized generation or handling of Personal Identifiable Information (PII) that 
Evidence:
  - "Personal data of users of the AI system being inadvertently revealed by the outputs of the system itself."

### [medium] ai-risk-taxonomy-unauthorized-inference/synthesis---pii-(personal-identifiable-information) — Unauthorized inference/synthesis - PII (Personal Identifiable Information)
Description: Unauthorized inference/synthesis - PII (Personal Identifiable Information) is defined as if the model response potentially facilitates privacy violations or unauthorized synthesis of personal identifi
Evidence:
  - "Personal data of users of the AI system being inadvertently revealed by the outputs of the system itself."

### [medium] ai-risk-taxonomy-unauthorized-processing---pii-(personal-identifiable-information) — Unauthorized processing - PII (Personal Identifiable Information)
Description: Unauthorized processing - PII (Personal Identifiable Information) is defined as if the model response involves unauthorized processing or misuse of Personal Identifiable Information (PII) in any form.
Evidence:
  - "Input of Trust sensitive and proprietary data outside of those approved in 5.6.2 into public, free or publicly available AI tools such as ChatGPT or OSINT tools will be considered a data breach."

### [medium] atlas-data-curation — Improper data curation
Description: Improper collection, generation, and preparation of training or tuning data can result in data label errors, conflicting information or misinformation.
Evidence:
  - "For existing data sets to train the AI system, colleagues must assess the quantity and suitability of available data that will be needed by the system."

### [medium] atlas-direct-instructions-attack — Direct instructions attack
Description: Prompts, questions, or requests designed to elicit undesirable responses from the application. This approach directly instructs the model to engage in the undesired behavior.
Evidence:
  - "Ensure that adversarial scenarios are tested against solutions to ensure resilience in the face of manipulative attacks."

### [medium] atlas-improper-usage — Improper usage
Description: Improper usage occurs when a model is used for a purpose that it was not originally designed for.
Evidence:
  - "Passing off work generated by AI is not acceptable, and will be treated as seriously as plagiarism."

### [medium] atlas-incomplete-advice — Incomplete advice
Description: When a model provides advice without having enough information, resulting in possible harm if the advice is followed.
Evidence:
  - "LLMs should not be used to make medical diagnoses or to provide medical advice if not approved for use as medical device."

### [medium] atlas-unexplainable-output — Unexplainable output
Description: Explanations for model output decisions might be difficult, imprecise, or not possible to obtain.
Evidence:
  - "Appropriate Transparency and Explainability"
  - "They can sometimes generate incorrect or misleading information that can appear correct."

### [medium] atlas-unrepresentative-data — Unrepresentative data
Description: Unrepresentative data occurs when the training or fine-tuning data is not sufficiently representative of the underlying population or does not measure the phenomenon of interest. Synthetic data might 
Evidence:
  - "AI Assurance Landscape including data quality and decision making"

### [medium] credo-risk-018 — AI deception
Description: The AI system may misrepresent its own capabilities or limitations, potentially leading to misplaced trust or inappropriate
Evidence:
  - "They can sometimes generate incorrect or misleading information that can appear correct."
  - "LLMs are trained on massive datasets of text and code, and are still under development. They can sometimes generate incorrect or misleading information that can appear correct."

### [medium] credo-risk-019 — Loss of human agency and autonomy (Slattery et al., 2024; IBM, 2024)
Description: The AI system may make decisions that diminish human control and autonomy, potentially leading to humans feeling disempowered, losing the ability to shape a fulfilling life trajectory, or becoming cog
Evidence:
  - "LLM output must always be verified via human intervention."

### [medium] credo-risk-024 — Civil liability
Description: The AI system may cause harm against individuals or organizations that results in civil lawsuits, potentially relating to issues like defamation, negligence, or privacy violations.
Evidence:
  - "ensuring the safety of patients and the public and the protection of their rights; and upholding the Trust's probity with respect to legal obligations and standards of care."

### [medium] credo-risk-029 — Mass surveillance and privacy attacks (Slattery et al., 2024)
Description: Mass surveillance and privacy attacks: Unauthorized monitoring and privacy violation at scale
Evidence:
  - "surveillance concerns  [eg.RIPA]"
  - "Remember that providers can and do monitor conversations to improve their systems and ensure the content complies with their own policies and safety requirements."

### [medium] credo-risk-030 — Integration challenges with existing systems
Description: The AI system may face difficulties in incorporating into existing technological infrastructure, processes, or workflows, potentially leading to operational disruptions, data silos, or reduced efficie
Evidence:
  - "Don't integrate any AI technology with Trust systems without the correct due diligence and approval."
  - "Don't install or use a solution that will require an unauthorised change to Trust systems including desktops, firewall rules, etc."

### [medium] mit-ai-risk-subdomain-4.1 — Disinformation, surveillance, and influence at scale
Description: Using AI systems to conduct large-scale disinformation campaigns, malicious surveillance, or targeted and sophisticated automated censorship and propaganda, with the aim to manipulate political proces
Evidence:
  - "Remember that providers can and do monitor conversations to improve their systems and ensure the content complies with their own policies and safety requirements."

### [medium] mit-ai-risk-subdomain-5.2 — Loss of human agency and autonomy
Description: Humans delegating key decisions to AI systems, or AI systems making decisions that diminish human control and autonomy, potentially leading to humans feeling disempowered, losing the ability to shape 
Evidence:
  - "LLM output must always be verified via human intervention."
  - "Output from LLMs should be validated and correlated with other trusted sources of information. Fact-check all content."

### [medium] mit-ai-risk-subdomain-6.3 — Economic and cultural devaluation of human effort
Description: AI systems capable of creating economic or cultural value, including through reproduction of human innovation or creativity (e.g., art, music, writing, code, invention), can destabilize economic and s
Evidence:
  - "Passing off work generated by AI is not acceptable, and will be treated as seriously as plagiarism."

## icrc (7 high, 9 medium)

### [high] ai-risk-taxonomy-warfare — Warfare
Description: Warfare is defined as whether the model's response promotes or assists in activities related to violence, extremism, military actions, or warfare.
Evidence:
  - "do not use AI providers that (i) are directly engaged in activities contributing to armed conflict or closely associated with military activities of parties to conflict"

### [high] credo-risk-008 — Opaque system architecture
Description: The AI system's internal structure and decision-making process may not be understandable or accessible to stakeholders, including developers, auditors, or end-users.
Evidence:
  - "Transparency and 'explainability' are essential elements of a safe, ethical and responsible approach to AI"
  - "explanations on the causal link between AI inputs and outputs and the functioning of algorithmic processes."

### [high] credo-risk-009 — Black box decisionmaking (Slattery et al., 2024; IBM, 2024)
Description: The AI system's decision-making process may be opaque, even when the architecture is known, making it difficult to understand how the system arrives at its outputs or recommendations.
Evidence:
  - "explanations on the causal link between AI inputs and outputs and the functioning of algorithmic processes."
  - "This includes adequate and meaningful information about why, when and how AI solutions are used, and explanations on the causal link between AI inputs and outputs and the functioning of algorithmic processes."

### [high] credo-risk-011 — Disparate model performance (Slattery et al., 2024; IBM, 2024)
Description: The AI system may exhibit unjustified or harmful differences in accuracy, quality, or outcomes across demographic groups, potentially leading to unfair treatment and discrimination. This includes both
Evidence:
  - "The ICRC acknowledges the significant risks of AI systems that could generate false or inaccurate data and replicate or amplify systemic and societal discriminations, biases and stereotypes - in particular around gender and race."
  - "The ICRC makes all possible efforts to ensure that the AI solutions and tools we use are inclusive by design and in their impact, and that they enable fair, non-discriminatory, equal and equitable delivery of assistance and services to all affected people and users, taking into account the varying degrees of need and capacity."

### [high] credo-risk-029 — Mass surveillance and privacy attacks (Slattery et al., 2024)
Description: Mass surveillance and privacy attacks: Unauthorized monitoring and privacy violation at scale
Evidence:
  - "Considering the multiple and significant risks that AI solutions present for the confidentiality and protection of the data that the ICRC collects, processes and manages for the purposes of our activities"
  - "Mechanisms are put in place to ensure that the data required for AI systems is collected, used, shared, archived and deleted in ways that are consistent with the right to privacy of affected people and users."

### [high] mit-ai-risk-subdomain-1.3 — Unequal performance across groups
Description: Accuracy and effectiveness of AI decisions and actions is dependent on group membership, where decisions in AI system design and biased training data lead to unequal outcomes, reduced benefits, increa
Evidence:
  - "The ICRC acknowledges the significant risks of AI systems that could generate false or inaccurate data and replicate or amplify systemic and societal discriminations, biases and stereotypes - in particular around gender and race."
  - "The ICRC makes all possible efforts to ensure that the AI solutions and tools we use are inclusive by design and in their impact, and that they enable fair, non-discriminatory, equal and equitable delivery of assistance and services to all affected people and users, taking into account the varying degrees of need and capacity."

### [high] mit-ai-risk-subdomain-7.3 — Lack of capability or robustness
Description: AI systems that fail to perform reliably or effectively under varying conditions, exposing them to errors and failures that can have significant consequences, especially in critical applications or ar
Evidence:
  - "The technical complexity and potential risks attached to AI systems and their functioning requires a significant level of knowledge and expertise to select, operate and manage them effectively and responsibly."
  - "The necessary evidence is gathered through scientific experimentation and 'sandbox' testing to ensure, as far as possible, the effectiveness and safety of the solutions in context."

### [medium] atlas-unrepresentative-data — Unrepresentative data
Description: Unrepresentative data occurs when the training or fine-tuning data is not sufficiently representative of the underlying population or does not measure the phenomenon of interest. Synthetic data might 
Evidence:
  - "The ICRC acknowledges the significant risks of AI systems that could generate false or inaccurate data and replicate or amplify systemic and societal discriminations, biases and stereotypes - in particular around gender and race."

### [medium] credo-risk-005 — Lack of training data transparency (IBM, 2024)
Description: Without accurate documentation on how a model's data was collected, curated, and used to train a model, it may be harder to satisfactorily explain the behavior of the model with respect to the data. D
Evidence:
  - "Additional systematic data quality control and meaningful and effective human oversight mechanisms are put in place to control and review relevant training models, algorithmic systems, inputs and outputs throughout the lifecycle of AI solutions used to support operational activities and decision-making processes that have an impact and present a risk of harm for affected people and users."

### [medium] credo-risk-024 — Civil liability
Description: The AI system may cause harm against individuals or organizations that results in civil lawsuits, potentially relating to issues like defamation, negligence, or privacy violations.
Evidence:
  - "the potential negative or harmful consequences arising from them"
  - "when they involve legal or reputational risks for the organization."
  - "potential impact on the safety, dignity and rights of affected populations and users"

### [medium] credo-risk-025 — Corporate liability (IBM, 2024)
Description: The AI system's use may lead to legal action or penalties against corporations for intellectual property infringement, AI-related misconduct, violations of fiduciary duty, or failure to adequately ove
Evidence:
  - "when they involve legal or reputational risks for the organization."

### [medium] credo-risk-027 — Cyberattacks, weapon development, and mass harm (AI, 2023; IBM, 2024)
Description: The AI system may be misused for developing malicious software, lethal autonomous weapons, or planning large-scale harmful activities.
Evidence:
  - "Risks of misuse, abuse, infiltration and attacks against AI systems and potential related harms and damage are systematically considered"

### [medium] credo-risk-033 — Lack of adequate capabilities (Slattery et al., 2024; IBM, 2024; AI, 2023)
Description: The AI system may fail to achieve required performance levels due to fundamental technological limitations or insufficient resources, potentially leading to suboptimal or unreliable outcomes.
Evidence:
  - "Its implementation will require investments in specific operational and governance capabilities, within the limits of the ICRC's operational and financial capacities."
  - "The technical complexity and potential risks attached to AI systems and their functioning requires a significant level of knowledge and expertise to select, operate and manage them effectively and responsibly."

### [medium] credo-risk-035 — Lack of robustness (Slattery et al., 2024)
Description: The AI system's performance may fail to generalize well to new environments or inputs, potentially leading to unexpected failures or degraded performance in real-world applications.
Evidence:
  - "When the potential benefits of AI outweigh identified risks, solutions under consideration are thoroughly tested before being rolled out. The necessary evidence is gathered through scientific experimentation and 'sandbox' testing to ensure, as far as possible, the effectiveness and safety of the solutions in context."

### [medium] credo-risk-040 — AI-generated security weaknesses (Slattery et al., 2024; IBM, 2024; AI, 2023)
Description: AI system security vulnerabilities: Implementation weaknesses in AI system architecture and infrastructure
Evidence:
  - "Risks of misuse, abuse, infiltration and attacks against AI systems and potential related harms and damage are systematically considered, and the highest possible standards of data protection and cybersecurity measures are put in place to prevent and mitigate them, in line with assessed risk levels."

### [medium] credo-risk-045 — Competitive dynamics (Slattery et al., 2024)
Description: The AI system's rapid development
Evidence:
  - "the speed and scale of AI-related innovations in the past few years, the emergence of new technological tools, their simplified accessibility, push-and-pull factors inside and outside the ICRC, and ongoing debates about the opportunities and risks they create - including for humanitarian action - have triggered a need to ensure that the organization is adequately equipped to explore and manage these developments in a timely, coherent and responsible manner."

## leicestershire_police (20 high, 10 medium)

### [high] ai-risk-taxonomy-characterization-of-identity---age — Characterization of identity - Age
Description: Characterization of identity - Age is defined as if the model response promotes or perpetuates age-related stereotypes or biases.
Evidence:
  - "Ensures outputs do not discriminate based on age."
  - "Encourages review of content to avoid age-related bias."

### [high] ai-risk-taxonomy-characterization-of-identity---beliefs — Characterization of identity - Beliefs
Description: Characterization of identity - Beliefs is defined as if the model response perpetuates, reinforces, or fails to adequately address stereotypes and biases related to protected characteristics, particul
Evidence:
  - "Encourages sensitivity in AI-generated content and prohibits offensive or inappropriate outputs."

### [high] ai-risk-taxonomy-characterization-of-identity---disability — Characterization of identity - Disability
Description: Characterization of identity - Disability is defined as if the model's response appropriately handles the portrayal of individuals with disabilities without perpetuating stereotypes or biases.
Evidence:
  - "Supports productivity for staff with disabilities through features like summarisation and drafting. Encourages review to avoid discriminatory content."

### [high] ai-risk-taxonomy-characterization-of-identity---gender — Characterization of identity - Gender
Description: Characterization of identity - Gender is defined as if the model response appropriately handles the characterization of identity related to gender without promoting or perpetuating discrimination or b
Evidence:
  - "Promotes fair representation and requires users to identify and correct biased outputs."
  - "Reinforces respectful and inclusive language. Promotes awareness of potential bias in AI-generated content."

### [high] ai-risk-taxonomy-characterization-of-identity---pregnancy-status — Characterization of identity - Pregnancy Status
Description: Characterization of identity - Pregnancy Status is defined as if the model's response promotes or supports discriminatory practices or biases based on pregnancy status.
Evidence:
  - "Prevents misuse of AI in ways that could expose or mishandle personal data related to pregnancy or maternity."

### [high] ai-risk-taxonomy-characterization-of-identity---religion — Characterization of identity - Religion
Description: Characterization of identity - Religion is defined as if the model's response potentially perpetuates or challenges discrimination or bias based on religious identity.
Evidence:
  - "Encourages sensitivity in AI-generated content and prohibits offensive or inappropriate outputs."

### [high] ai-risk-taxonomy-classification-of-individuals---age — Classification of individuals - Age
Description: Classification of individuals - Age is defined as if the model response involves classifying or sorting individuals based on age, which is a protected characteristic and can lead to discrimination or 
Evidence:
  - "Promotes inclusive use of AI tools and ensures outputs do not discriminate based on age."

### [high] ai-risk-taxonomy-classification-of-individuals---gender — Classification of individuals - Gender
Description: Classification of individuals - Gender is defined as if the model's response promotes, reinforces, or fails to adequately address issues related to gender discrimination or bias.
Evidence:
  - "Acknowledges potential for gender bias in AI tools."
  - "Promotes fair representation and requires users to identify and correct biased outputs."

### [high] ai-risk-taxonomy-classification-of-individuals---race — Classification of individuals - Race
Description: Classification of individuals - Race is defined as if the model response promotes or perpetuates racial discrimination or bias, particularly in the classification of individuals based on race.
Evidence:
  - "Recognises the risk of racial bias in AI outputs."
  - "Promotes vigilance and correction of racially biased content."

### [high] ai-risk-taxonomy-discrimination-in-employment,-benefits,-or-services---age — Discrimination in employment, benefits, or services - Age
Description: Discrimination in employment, benefits, or services - Age is defined as if the model's response subtly encourages or facilitates age discrimination in employment, benefits, or services.
Evidence:
  - "Promotes inclusive use of AI tools and ensures outputs do not discriminate based on age. Encourages review of content to avoid age-related bias."

### [high] ai-risk-taxonomy-discrimination-in-employment,-benefits,-or-services---beliefs — Discrimination in employment, benefits, or services - Beliefs
Description: Discrimination in employment, benefits, or services - Beliefs is defined as if the model response subtly encourages or implements discriminatory practices based on political beliefs in employment, ben
Evidence:
  - "Encourages sensitivity in AI-generated content and prohibits offensive or inappropriate outputs."

### [high] ai-risk-taxonomy-discrimination-in-employment,-benefits,-or-services---disability — Discrimination in employment, benefits, or services - Disability
Description: Discrimination in employment, benefits, or services - Disability is defined as if the model's response promotes or facilitates discrimination against individuals with disabilities in employment, benef
Evidence:
  - "Supports productivity for staff with disabilities through features like summarisation and drafting. Encourages review to avoid discriminatory content."

### [high] ai-risk-taxonomy-discrimination-in-employment,-benefits,-or-services---gender — Discrimination in employment, benefits, or services - Gender
Description: Discrimination in employment, benefits, or services - Gender is defined as if the model response promotes or justifies gender-based discrimination in employment, benefits, or services.
Evidence:
  - "Acknowledges potential for gender bias in AI tools."
  - "Promotes fair representation and requires users to identify and correct biased outputs."

### [high] ai-risk-taxonomy-discrimination-in-employment,-benefits,-or-services---pregnancy-status — Discrimination in employment, benefits, or services - Pregnancy Status
Description: Discrimination in employment, benefits, or services - Pregnancy Status is defined as if the model response promotes or facilitates discrimination against pregnant women in employment, benefits, or ser
Evidence:
  - "Prevents misuse of AI in ways that could expose or mishandle personal data related to pregnancy or maternity."

### [high] ai-risk-taxonomy-discrimination-in-employment,-benefits,-or-services---race — Discrimination in employment, benefits, or services - Race
Description: Discrimination in employment, benefits, or services - Race is defined as if the model's response subtly or overtly supports discriminatory practices based on race in employment, benefits, or services.
Evidence:
  - "Recognises the risk of racial bias in AI outputs."
  - "Promotes vigilance and correction of racially biased content. Supports equality by requiring review and transparency."

### [high] ai-risk-taxonomy-discrimination-in-employment,-benefits,-or-services---religion — Discrimination in employment, benefits, or services - Religion
Description: Discrimination in employment, benefits, or services - Religion is defined as if the model response facilitates or supports discrimination based on religious affiliations in employment, benefits, or se
Evidence:
  - "Encourages sensitivity in AI-generated content and prohibits offensive or inappropriate outputs."

### [high] ai-risk-taxonomy-discrimination-in-employment,-benefits,-or-services---sexual-orientation — Discrimination in employment, benefits, or services - Sexual orientation
Description: Discrimination in employment, benefits, or services - Sexual orientation is defined as whether the model's response facilitates or supports discrimination based on sexual orientation, particularly in 
Evidence:
  - "Recognises risk of underrepresentation or"

### [high] atlas-spreading-disinformation — Spreading disinformation
Description: Generative AI models might be used to intentionally create misleading or false information to deceive or influence a targeted audience.
Evidence:
  - "AI tools can produce inaccurate, misleading, or fabricated information-commonly referred to as "hallucinations.""
  - "AI Models, Including LLM's, can sometimes 'hallucinate'-this means they may generate information that sounds plausible but is actually incorrect, made up, or not supported by real data."

### [high] atlas-unrepresentative-data — Unrepresentative data
Description: Unrepresentative data occurs when the training or fine-tuning data is not sufficiently representative of the underlying population or does not measure the phenomenon of interest. Synthetic data might 
Evidence:
  - "AI systems may reflect or amplify societal biases present in their training data. This can result in unintended reinforcement of stereotypes related to gender, race, profession, or other protected characteristics."
  - "Certain groups may be disproportionately represented-or excluded-in Al-generated outputs."

### [high] mit-ai-risk-subdomain-5.2 — Loss of human agency and autonomy
Description: Humans delegating key decisions to AI systems, or AI systems making decisions that diminish human control and autonomy, potentially leading to humans feeling disempowered, losing the ability to shape 
Evidence:
  - "AI must not be allowed to make operational decisions without human review."
  - "AI should support, not replace, professional judgment, especially in sensitive situations."
  - "However, the responsibility and liability remain with the police decision maker."

### [medium] ai-risk-taxonomy-characterization-of-identity---sexual-orientation — Characterization of identity - Sexual orientation
Description: Characterization of identity - Sexual orientation is defined as if the model's response appropriately addresses the complexity of discrimination or bias based on sexual orientation while considering i
Evidence:
  - "Recognises risk of underrepresentation or"

### [medium] ai-risk-taxonomy-classification-of-individuals---beliefs — Classification of individuals - Beliefs
Description: Classification of individuals - Beliefs is defined as if the model response involves classifying or profiling individuals based on their beliefs or protected characteristics.
Evidence:
  - "Encourages sensitivity in AI-generated content and prohibits offensive or inappropriate outputs."

### [medium] ai-risk-taxonomy-classification-of-individuals---religion — Classification of individuals - Religion
Description: Classification of individuals - Religion is defined as if the model response involves classifying or inferring individuals' religious beliefs based on their behavior, speech, or other personal charact
Evidence:
  - "Encourages sensitivity in AI-generated content and prohibits offensive or inappropriate outputs."

### [medium] ai-risk-taxonomy-classification-of-individuals---sexual-orientation — Classification of individuals - Sexual orientation
Description: Classification of individuals - Sexual orientation is defined as if the model engages in discriminatory or biased behavior by attempting to classify or predict an individual's sexual orientation based
Evidence:
  - "Recognises risk of underrepresentation or"

### [medium] ai-risk-taxonomy-classification-of-individuals---social-behaviors — Classification of individuals - Social behaviors
Description: Classification of individuals - Social behaviors is defined as if the model response promotes or supports discrimination or bias based on protected characteristics such as gender, age, ethnicity, soci
Evidence:
  - "Promotes inclusive use of AI tools and ensures outputs do not discriminate based on age."
  - "Promotes fair representation and requires users to identify and correct biased outputs."

### [medium] ai-risk-taxonomy-discrimination-in-employment,-benefits,-or-services---ethnicity — Discrimination in employment, benefits, or services - Ethnicity
Description: Discrimination in employment, benefits, or services - Ethnicity is defined as if the model's response facilitates or supports discriminatory practices based on ethnicity in employment, benefits, or se
Evidence:
  - "Recognises the risk of racial bias in AI outputs."
  - "Promotes vigilance and correction of racially biased content."

### [medium] ai-risk-taxonomy-discrimination-in-employment,-benefits,-or-services---health-conditions — Discrimination in employment, benefits, or services - Health conditions
Description: Discrimination in employment, benefits, or services - Health conditions is defined as if the model's response subtly or overtly discriminates against individuals based on health conditions in scenario
Evidence:
  - "Supports productivity for staff with disabilities through features like summarisation and drafting."

### [medium] atlas-improper-usage — Improper usage
Description: Improper usage occurs when a model is used for a purpose that it was not originally designed for.
Evidence:
  - "The use of AI technologies is not yet authorised for use in the Criminal Justice process, including for the creation of evidential materials."
  - "Do not use it for legal interpretation, risk assessments, or direct public communication without review."

### [medium] atlas-toxic-output — Toxic output
Description: Toxic output occurs when the model produces hateful, abusive, and profane (HAP) or obscene content. This also includes behaviors like bullying.
Evidence:
  - "Be alert to potential bias, stereotyping, or inappropriate content in AI outputs."

### [medium] credo-risk-024 — Civil liability
Description: The AI system may cause harm against individuals or organizations that results in civil lawsuits, potentially relating to issues like defamation, negligence, or privacy violations.
Evidence:
  - "the responsibility and liability remain with the police decision maker."
  - "AI can never be used as a defence or rationale for a poor decision."

## lenovo (7 high, 12 medium)

### [high] atlas-confidential-data-in-prompt — Confidential data in prompt
Description: Confidential information might be included as a part of the prompt that is sent to the model.
Evidence:
  - "We will ensure that our AI systems are not given inappropriate information or prompts, including: (1) third-party information in Lenovo's control not authorized for such use, (2) Lenovo confidential or restricted information, if the AI system is not approved for such use"

### [high] atlas-data-bias — Data bias
Description: Historical and societal biases might be present in data that are used to train and fine-tune models. Biases can also be inherited from seed data or exacerbated by synthetic data generation methods.
Evidence:
  - "We will regularly review and address potential biases in AI algorithms, data sources, and decision-making frameworks to ensure fairness and equitable outcomes."
  - "In determining whether to develop, use, or implement an AI system, Lenovo will evaluate it (e.g., data sets, algorithms, user interfaces) to ensure the AI system mitigates bias and ensures fair and equal treatment for all users."

### [high] atlas-exclusion — Exclusion
Description: Exclusion refers to the risk that synthetic data generation processes may overlook or fail to consult with marginalized populations. Such exclusion results in synthetic data that does not accurately r
Evidence:
  - "AI systems will be designed in a manner that avoids unfair biases, protects against the marginalization of vulnerable groups, and guards against prejudice and discrimination."

### [high] atlas-unexplainable-output — Unexplainable output
Description: Explanations for model output decisions might be difficult, imprecise, or not possible to obtain.
Evidence:
  - "We will strive to create and use AI systems that are explainable."
  - "Explainable AI uses processes and methods that allow users to understand, in a meaningful way, the facts and inferences behind an AI system's action."

### [high] credo-risk-005 — Lack of training data transparency (IBM, 2024)
Description: Without accurate documentation on how a model's data was collected, curated, and used to train a model, it may be harder to satisfactorily explain the behavior of the model with respect to the data. D
Evidence:
  - "The data sets and processes that yield the AI system's decisions, including data gathering, data labeling, and any algorithms used, should be documented to allow for traceability and transparency."
  - "They should also have measures in place to continuously assess the quality and sourcing of the data input into the AI system."

### [high] credo-risk-029 — Mass surveillance and privacy attacks (Slattery et al., 2024)
Description: Mass surveillance and privacy attacks: Unauthorized monitoring and privacy violation at scale
Evidence:
  - "Lenovo prohibits AI systems that: (d) use or were trained on biometric data indiscriminately scraped from social media or publicly-available information, or (e) involve the collection of sensitive personal data to enable profiling of individuals."

### [high] mit-ai-risk-subdomain-6.3 — Economic and cultural devaluation of human effort
Description: AI systems capable of creating economic or cultural value, including through reproduction of human innovation or creativity (e.g., art, music, writing, code, invention), can destabilize economic and s
Evidence:
  - "Examples include use of generative AI to create code, content, or materials"
  - "In order to be protected as intellectual property, the results and decisions of AI systems may not be treated as the direct final product to be used by Lenovo or presented outside Lenovo."
  - "These materials are created by and the responsibility of humans, even where AI systems help in their creation."

### [medium] atlas-copyright-infringement — Copyright infringement
Description: A model might generate content that is similar or identical to existing work protected by copyright or covered by open-source license agreement.
Evidence:
  - "We will ensure that our AI systems are not given inappropriate information or prompts, including: (1) third-party information in Lenovo's control not authorized for such use, (2) Lenovo confidential or restricted information, if the AI system is not approved for such use, (3) personal information of Lenovo employees, customers, or others who have not explicitly consented to such use, or (4) prompts or directions that would tend to create problematic, biased, or infringing results."

### [medium] atlas-data-curation — Improper data curation
Description: Improper collection, generation, and preparation of training or tuning data can result in data label errors, conflicting information or misinformation.
Evidence:
  - "They should also have measures in place to continuously assess the quality and sourcing of the data input into the AI system."
  - "The data sets and processes that yield the AI system's decisions, including data gathering, data labeling, and any algorithms used, should be documented to allow for traceability and transparency."

### [medium] atlas-improper-usage — Improper usage
Description: Improper usage occurs when a model is used for a purpose that it was not originally designed for.
Evidence:
  - "We will ensure that our AI systems are not given inappropriate information or prompts, including: (1) third-party information in Lenovo's control not authorized for such use, (2) Lenovo confidential or restricted information, if the AI system is not approved for such use"

### [medium] atlas-nonconsensual-use — Nonconsensual use
Description: Generative AI models might be intentionally used to imitate people through deepfakes by using video, images, audio, or other modalities without their consent.
Evidence:
  - "personal information of Lenovo employees, customers, or others who have not explicitly consented to such use"

### [medium] atlas-poor-model-accuracy — Poor model accuracy
Description: Poor model accuracy occurs when a model's performance is insufficient to the task it was designed for. Low accuracy might occur if the model is not correctly engineered, or if the model's expected inp
Evidence:
  - "Technical robustness and safety require that AI systems preemptively address risks including, but not limited to, the unpredictability of AI performance and cybersecurity."

### [medium] atlas-unrepresentative-data — Unrepresentative data
Description: Unrepresentative data occurs when the training or fine-tuning data is not sufficiently representative of the underlying population or does not measure the phenomenon of interest. Synthetic data might 
Evidence:
  - "We will regularly review and address potential biases in AI algorithms, data sources, and decision-making frameworks to ensure fairness and equitable outcomes."

### [medium] credo-risk-018 — AI deception
Description: The AI system may misrepresent its own capabilities or limitations, potentially leading to misplaced trust or inappropriate
Evidence:
  - "We will establish mechanisms to ensure transparency of the capabilities and limitations on AI systems to ensure users can make informed choices about them."

### [medium] credo-risk-026 — Fraud, scams, and targeted manipulation
Description: The AI system may be exploited to facilitate fraudulent activities, scams, or targeted manipulation, including generating deepfakes and enhancing phishing attacks.
Evidence:
  - "Lenovo prohibits AI systems that: (a) deploy subliminal or manipulative techniques, (b) exploit a person's vulnerabilities"

### [medium] credo-risk-027 — Cyberattacks, weapon development, and mass harm (AI, 2023; IBM, 2024)
Description: The AI system may be misused for developing malicious software, lethal autonomous weapons, or planning large-scale harmful activities.
Evidence:
  - "Technical robustness and safety require that AI systems preemptively address risks including, but not limited to, the unpredictability of AI performance and cybersecurity."

### [medium] credo-risk-033 — Lack of adequate capabilities (Slattery et al., 2024; IBM, 2024; AI, 2023)
Description: The AI system may fail to achieve required performance levels due to fundamental technological limitations or insufficient resources, potentially leading to suboptimal or unreliable outcomes.
Evidence:
  - "Technical robustness and safety require that AI systems preemptively address risks including, but not limited to, the unpredictability of AI performance and cybersecurity."
  - "We will appropriately test, validate, and implement mechanisms to detect and rectify biases, errors, or unintended consequences in AI systems."

### [medium] credo-risk-040 — AI-generated security weaknesses (Slattery et al., 2024; IBM, 2024; AI, 2023)
Description: AI system security vulnerabilities: Implementation weaknesses in AI system architecture and infrastructure
Evidence:
  - "Technical robustness and safety require that AI systems preemptively address risks including, but not limited to, the unpredictability of AI performance and cybersecurity."

### [medium] mit-ai-risk-subdomain-7.1 — AI pursuing its own goals in conflict with human goals or values
Description: AI systems acting in conflict with human goals or values, especially the goals of designers or users, or ethical standards. These misaligned behaviors may be introduced by humans during design and dev
Evidence:
  - "Lenovo prohibits AI systems that: (a) deploy subliminal or manipulative techniques, (b) exploit a person's vulnerabilities"
  - "AI systems that pose a significant risk to a person's health, safety, or civil rights will be evaluated with additional scrutiny and risk-mitigation analysis."

## llvm (5 high, 4 medium)

### [high] atlas-bypassing-learning — Impact on education: bypassing learning
Description: Easy access to high-quality generative models might result in students that use AI models to bypass the learning process.
Evidence:
  - "Whether you are a newcomer or not, fully automating the process of fixing this issue squanders the learning opportunity and doesn't add much value to the project."

### [high] atlas-data-usage-rights — Data usage rights restrictions
Description: Terms of service, license compliance, or other IP issues may restrict the ability to use certain data for building models.
Evidence:
  - "Using AI tools to regenerate copyrighted material does not remove the copyright, and contributors are responsible for ensuring that such material does not appear in their contributions."

### [high] credo-risk-002 — AI pursuing its own goals in conflict with human goals or values (Slattery et al., 2024)
Description: The AI system may act in conflict with ethical standards or human goals or values, especially those of its designers or users, potentially using dangerous capabilities such as manipulation, deception,
Evidence:
  - "it bans agents that take action in our digital spaces without human approval"

### [high] credo-risk-005 — Lack of training data transparency (IBM, 2024)
Description: Without accurate documentation on how a model's data was collected, curated, and used to train a model, it may be harder to satisfactorily explain the behavior of the model with respect to the data. D
Evidence:
  - "Using AI tools to regenerate copyrighted material does not remove the copyright, and contributors are responsible for ensuring that such material does not appear in their contributions."

### [high] credo-risk-039 — AI model and intellectual property theft
Description: AI model and intellectual property theft - Unauthorized copying of trained models and associated AI intellectual property
Evidence:
  - "Artificial intelligence systems raise many questions around copyright that have yet to be answered."
  - "Using AI tools to regenerate copyrighted material does not remove the copyright, and contributors are responsible for ensuring that such material does not appear in their contributions."

### [medium] atlas-model-usage-rights — Model usage rights restrictions
Description: Terms of service, licenses, or other rules restrict the use of certain models.
Evidence:
  - "This PR doesn't appear to comply with our policy on tool-generated content, and requires additional justification for why it is valuable enough to the project for us to review it."
  - "QEMU bans use of AI content generators"

### [medium] credo-risk-042 — Increased inequality and decline in employment quality (Slattery et al., 2024; IBM, 2024)
Description: The AI system's widespread use may cause social and economic inequalities by automating jobs, reducing employment quality, or producing exploitative dependencies between workers and their employers.
Evidence:
  - "Sending the unreviewed output of an LLM to open source project maintainers *extracts* work from them in the form of design and code review, so we call this kind of contribution an "extractive contribution"."
  - "While new tools enable more development, it shifts effort from the implementor to the reviewer, and our policy exists to ensure that we value and do not squander maintainer time."

### [medium] mit-ai-risk-subdomain-2.2 — AI system security vulnerabilities and attacks
Description: Vulnerabilities in AI systems, software development toolchains, and hardware that can be exploited, resulting in unauthorized access, data and privacy breaches, or system manipulation causing unsafe o
Evidence:
  - "Seth Larson's post on slop security reports in the Python ecosystem"

### [medium] mit-ai-risk-subdomain-7.3 — Lack of capability or robustness
Description: AI systems that fail to perform reliably or effectively under varying conditions, exposing them to errors and failures that can have significant consequences, especially in critical applications or ar
Evidence:
  - "Contributors must read and review all LLM-generated code or text before they ask other project members to review it."

## lse-legreg (16 high, 35 medium)

### [high] ai-risk-taxonomy-characterization-of-identity---disability — Characterization of identity - Disability
Description: Characterization of identity - Disability is defined as if the model's response appropriately handles the portrayal of individuals with disabilities without perpetuating stereotypes or biases.
Evidence:
  - "The Equality Act also places a duty on employers to ensure that reasonable adjustments are made to reduce or remove disadvantages that may be faced by people with disabilities."

### [high] ai-risk-taxonomy-characterization-of-identity---race — Characterization of identity - Race
Description: Characterization of identity - Race is defined as if the model's response potentially perpetuates or reinforces stereotypes or biases related to race, gender, or other protected characteristics.
Evidence:
  - "The Equality Act 2010 prohibits both direct and indirect discrimination on the grounds of protected characteristics. These are sex, race, age, religion, disability, sexual orientation, pregnancy/maternity, gender reassignment and marriage/civil partnership."
  - "In addition, the use of AI tools to process decisions and generate outputs may lead to discrimination based on protected characteristics."

### [high] ai-risk-taxonomy-characterization-of-identity---religion — Characterization of identity - Religion
Description: Characterization of identity - Religion is defined as if the model's response potentially perpetuates or challenges discrimination or bias based on religious identity.
Evidence:
  - "The Equality Act 2010 prohibits both direct and indirect discrimination on the grounds of protected characteristics. These are sex, race, age, religion, disability, sexual orientation, pregnancy/maternity, gender reassignment and marriage/civil partnership."
  - "In addition, the use of AI tools to process decisions and generate outputs may lead to discrimination based on protected characteristics."

### [high] ai-risk-taxonomy-classification-of-individuals---gender — Classification of individuals - Gender
Description: Classification of individuals - Gender is defined as if the model's response promotes, reinforces, or fails to adequately address issues related to gender discrimination or bias.
Evidence:
  - "These are sex, race, age, religion, disability, sexual orientation, pregnancy/maternity, gender reassignment and marriage/civil partnership."
  - "In addition, the use of AI tools to process decisions and generate outputs may lead to discrimination based on protected characteristics."

### [high] ai-risk-taxonomy-classification-of-individuals---health-conditions — Classification of individuals - Health conditions
Description: Classification of individuals - Health conditions is defined as if the model response inappropriately classifies or discriminates against an individual based on health conditions.
Evidence:
  - "The Equality Act also places a duty on employers to ensure that reasonable adjustments are made to reduce or remove disadvantages that may be faced by people with disabilities."
  - "In addition, the use of AI tools to process decisions and generate outputs may lead to discrimination based on protected characteristics."

### [high] ai-risk-taxonomy-classification-of-individuals---pregnancy-status — Classification of individuals - Pregnancy Status
Description: Classification of individuals - Pregnancy Status is defined as if the model response engages in discriminatory practices or biases, specifically regarding the classification of individuals based on pr
Evidence:
  - "The Equality Act 2010 prohibits both direct and indirect discrimination on the grounds of protected characteristics. These are sex, race, age, religion, disability, sexual orientation, pregnancy/maternity, gender reassignment and marriage/civil partnership."
  - "In addition, the use of AI tools to process decisions and generate outputs may lead to discrimination based on protected characteristics."

### [high] ai-risk-taxonomy-classification-of-individuals---race — Classification of individuals - Race
Description: Classification of individuals - Race is defined as if the model response promotes or perpetuates racial discrimination or bias, particularly in the classification of individuals based on race.
Evidence:
  - "The Equality Act 2010 prohibits both direct and indirect discrimination on the grounds of protected characteristics. These are sex, race, age, religion, disability, sexual orientation, pregnancy/maternity, gender reassignment and marriage/civil partnership."
  - "In addition, the use of AI tools to process decisions and generate outputs may lead to discrimination based on protected characteristics."

### [high] ai-risk-taxonomy-classification-of-individuals---sexual-orientation — Classification of individuals - Sexual orientation
Description: Classification of individuals - Sexual orientation is defined as if the model engages in discriminatory or biased behavior by attempting to classify or predict an individual's sexual orientation based
Evidence:
  - "The Equality Act 2010 prohibits both direct and indirect discrimination on the grounds of protected characteristics. These are sex, race, age, religion, disability, sexual orientation, pregnancy/maternity, gender reassignment and marriage/civil partnership."
  - "In addition, the use of AI tools to process decisions and generate outputs may lead to discrimination based on protected characteristics."

### [high] ai-risk-taxonomy-discrimination-in-employment,-benefits,-or-services---ethnicity — Discrimination in employment, benefits, or services - Ethnicity
Description: Discrimination in employment, benefits, or services - Ethnicity is defined as if the model's response facilitates or supports discriminatory practices based on ethnicity in employment, benefits, or se
Evidence:
  - "These are sex, race, age, religion, disability, sexual orientation, pregnancy/maternity, gender reassignment and marriage/civil partnership."
  - "In addition, the use of AI tools to process decisions and generate outputs may lead to discrimination based on protected characteristics."

### [high] atlas-spreading-disinformation — Spreading disinformation
Description: Generative AI models might be used to intentionally create misleading or false information to deceive or influence a targeted audience.
Evidence:
  - "AI tools are known to hallucinate, namely supplying information that has no basis in reality, or else reproducing information that is out of date or is misinformation."

### [high] atlas-unexplainable-output — Unexplainable output
Description: Explanations for model output decisions might be difficult, imprecise, or not possible to obtain.
Evidence:
  - "Explainability: Where the output of an AI tool has influenced decision making or where an AI automated process is used, there should be someone appropriately trained and/ or informed to provide an explanation for how the AI tool has been used."
  - "appropriate transparency and explainability"

### [high] credo-risk-027 — Cyberattacks, weapon development, and mass harm (AI, 2023; IBM, 2024)
Description: The AI system may be misused for developing malicious software, lethal autonomous weapons, or planning large-scale harmful activities.
Evidence:
  - "Don't ask an AI tool to do something malicious or illegal."
  - "cybersecurity"

### [high] credo-risk-029 — Mass surveillance and privacy attacks (Slattery et al., 2024)
Description: Mass surveillance and privacy attacks: Unauthorized monitoring and privacy violation at scale
Evidence:
  - "Data Protection"
  - "Don't put personal data in an AI tool that is external to LSE."

### [high] credo-risk-039 — AI model and intellectual property theft
Description: AI model and intellectual property theft - Unauthorized copying of trained models and associated AI intellectual property
Evidence:
  - "Copyright and intellectual property"
  - "Don't upload in-copyright content (for example , images, photographs, student work, journal articles licensed from publishers by LSE library) where you do not have the copyright holder's permission and where the AI tool is known to use inputs as training data."

### [high] mit-ai-risk-subdomain-2.2 — AI system security vulnerabilities and attacks
Description: Vulnerabilities in AI systems, software development toolchains, and hardware that can be exploited, resulting in unauthorized access, data and privacy breaches, or system manipulation causing unsafe o
Evidence:
  - "cybersecurity"
  - "The School provides MS Copilot. This stays within the School's M365 tenancy so is safer to use as long as you have the correct access controls set on your information."

### [high] mit-ai-risk-subdomain-7.3 — Lack of capability or robustness
Description: AI systems that fail to perform reliably or effectively under varying conditions, exposing them to errors and failures that can have significant consequences, especially in critical applications or ar
Evidence:
  - "AI tools can produce unreliable information and where processes are automated, they may not adequately account for exceptions, mitigation or the need for reasonable adjustments."
  - "the information is based on large volumes of data, some of which can be inaccurate, biased, or discriminatory."

### [medium] ai-risk-taxonomy-characterization-of-identity---age — Characterization of identity - Age
Description: Characterization of identity - Age is defined as if the model response promotes or perpetuates age-related stereotypes or biases.
Evidence:
  - "The Equality Act 2010 prohibits both direct and indirect discrimination on the grounds of protected characteristics. These are sex, race, age, religion, disability, sexual orientation, pregnancy/maternity, gender reassignment and marriage/civil partnership."
  - "the use of AI tools to process decisions and generate outputs may lead to discrimination based on protected characteristics."

### [medium] ai-risk-taxonomy-characterization-of-identity---beliefs — Characterization of identity - Beliefs
Description: Characterization of identity - Beliefs is defined as if the model response perpetuates, reinforces, or fails to adequately address stereotypes and biases related to protected characteristics, particul
Evidence:
  - "The Equality Act 2010 prohibits both direct and indirect discrimination on the grounds of protected characteristics. These are sex, race, age, religion, disability, sexual orientation, pregnancy/maternity, gender reassignment and marriage/civil partnership."
  - "the use of AI tools to process decisions and generate outputs may lead to discrimination based on protected characteristics."

### [medium] ai-risk-taxonomy-characterization-of-identity---ethnicity — Characterization of identity - Ethnicity
Description: Characterization of identity - Ethnicity is defined as if the model's response potentially perpetuates or challenges stereotypes and biases related to ethnicity, particularly in professional or social
Evidence:
  - "The Equality Act 2010 prohibits both direct and indirect discrimination on the grounds of protected characteristics. These are sex, race, age, religion, disability, sexual orientation, pregnancy/maternity, gender reassignment and marriage/civil partnership."

### [medium] ai-risk-taxonomy-characterization-of-identity---gender — Characterization of identity - Gender
Description: Characterization of identity - Gender is defined as if the model response appropriately handles the characterization of identity related to gender without promoting or perpetuating discrimination or b
Evidence:
  - "The Equality Act 2010 prohibits both direct and indirect discrimination on the grounds of protected characteristics. These are sex, race, age, religion, disability, sexual orientation, pregnancy/maternity, gender reassignment and marriage/civil partnership."

### [medium] ai-risk-taxonomy-characterization-of-identity---health-conditions — Characterization of identity - Health conditions
Description: Characterization of identity - Health conditions is defined as if the model's response potentially perpetuates or challenges stereotypes and biases related to health conditions and their impact on pro
Evidence:
  - "The Equality Act also places a duty on employers to ensure that reasonable adjustments are made to reduce or remove disadvantages that may be faced by people with disabilities."
  - "AI tools can produce unreliable information and where processes are automated, they may not adequately account for exceptions, mitigation or the need for reasonable adjustments."

### [medium] ai-risk-taxonomy-characterization-of-identity---mental-characteristics — Characterization of identity - Mental Characteristics
Description: Characterization of identity - Mental Characteristics is defined as if the model's response potentially perpetuates stereotypes, shows bias, or discriminates based on mental characteristics or conditi
Evidence:
  - "The Equality Act 2010 prohibits both direct and indirect discrimination on the grounds of protected characteristics. These are sex, race, age, religion, disability, sexual orientation, pregnancy/maternity, gender reassignment and marriage/civil partnership."

### [medium] ai-risk-taxonomy-characterization-of-identity---occupation — Characterization of identity - Occupation
Description: Characterization of identity - Occupation is defined as if the model response appropriately addresses the discrimination or bias related to protected characteristics (such as race, gender, disability,
Evidence:
  - "The Equality Act also places a duty on employers to ensure that reasonable adjustments are made to reduce or remove disadvantages that may be faced by people with disabilities."
  - "In addition, the use of AI tools to process decisions and generate outputs may lead to discrimination based on protected characteristics."

### [medium] ai-risk-taxonomy-characterization-of-identity---predicted-personality — Characterization of identity - Predicted Personality
Description: Characterization of identity - Predicted Personality is defined as if the model's response potentially perpetuates or reinforces stereotypes based on protected characteristics such as race, gender, ag
Evidence:
  - "Profiling involves categorising people and predicting their behaviour based on their characteristics. This present discrimination risks."

### [medium] ai-risk-taxonomy-characterization-of-identity---pregnancy-status — Characterization of identity - Pregnancy Status
Description: Characterization of identity - Pregnancy Status is defined as if the model's response promotes or supports discriminatory practices or biases based on pregnancy status.
Evidence:
  - "The Equality Act 2010 prohibits both direct and indirect discrimination on the grounds of protected characteristics. These are sex, race, age, religion, disability, sexual orientation, pregnancy/maternity, gender reassignment and marriage/civil partnership."

### [medium] ai-risk-taxonomy-characterization-of-identity---sexual-orientation — Characterization of identity - Sexual orientation
Description: Characterization of identity - Sexual orientation is defined as if the model's response appropriately addresses the complexity of discrimination or bias based on sexual orientation while considering i
Evidence:
  - "The Equality Act 2010 prohibits both direct and indirect discrimination on the grounds of protected characteristics. These are sex, race, age, religion, disability, sexual orientation, pregnancy/maternity, gender reassignment and marriage/civil partnership."

### [medium] ai-risk-taxonomy-classification-of-individuals---beliefs — Classification of individuals - Beliefs
Description: Classification of individuals - Beliefs is defined as if the model response involves classifying or profiling individuals based on their beliefs or protected characteristics.
Evidence:
  - "These are sex, race, age, religion, disability, sexual orientation, pregnancy/maternity, gender reassignment and marriage/civil partnership."

### [medium] ai-risk-taxonomy-classification-of-individuals---color — Classification of individuals - Color
Description: Classification of individuals - Color is defined as if the model response engages in or promotes discrimination or bias based on skin color or protected characteristics.
Evidence:
  - "The Equality Act 2010 prohibits both direct and indirect discrimination on the grounds of protected characteristics. These are sex, race, age, religion, disability, sexual orientation, pregnancy/maternity, gender reassignment and marriage/civil partnership."
  - "the use of AI tools to process decisions and generate outputs may lead to discrimination based on protected characteristics."

### [medium] ai-risk-taxonomy-classification-of-individuals---ethnicity — Classification of individuals - Ethnicity
Description: Classification of individuals - Ethnicity is defined as if the model engages in discriminatory or biased behavior by classifying individuals based on ethnicity or protected characteristics.
Evidence:
  - "The Equality Act 2010 prohibits both direct and indirect discrimination on the grounds of protected characteristics. These are sex, race, age, religion, disability, sexual orientation, pregnancy/maternity, gender reassignment and marriage/civil partnership."
  - "Profiling involves categorising people and predicting their behaviour based on their characteristics. This present discrimination risks."

### [medium] ai-risk-taxonomy-classification-of-individuals---predicted-personality — Classification of individuals - Predicted Personality
Description: Classification of individuals - Predicted Personality is defined as if the model's response potentially discriminates or biases based on protected characteristics or predicts personality traits based 
Evidence:
  - "Profiling involves categorising people and predicting their behaviour based on their characteristics. This present discrimination risks."

### [medium] ai-risk-taxonomy-classification-of-individuals---religion — Classification of individuals - Religion
Description: Classification of individuals - Religion is defined as if the model response involves classifying or inferring individuals' religious beliefs based on their behavior, speech, or other personal charact
Evidence:
  - "The Equality Act 2010 prohibits both direct and indirect discrimination on the grounds of protected characteristics. These are sex, race, age, religion, disability, sexual orientation, pregnancy/maternity, gender reassignment and marriage/civil partnership."
  - "Profiling involves categorising people and predicting their behaviour based on their characteristics. This present discrimination risks."

### [medium] ai-risk-taxonomy-classification-of-individuals---social-behaviors — Classification of individuals - Social behaviors
Description: Classification of individuals - Social behaviors is defined as if the model response promotes or supports discrimination or bias based on protected characteristics such as gender, age, ethnicity, soci
Evidence:
  - "Profiling involves categorising people and predicting their behaviour based on their characteristics. This present discrimination risks."

### [medium] ai-risk-taxonomy-discrimination-in-employment,-benefits,-or-services---age — Discrimination in employment, benefits, or services - Age
Description: Discrimination in employment, benefits, or services - Age is defined as if the model's response subtly encourages or facilitates age discrimination in employment, benefits, or services.
Evidence:
  - "The Equality Act 2010 prohibits both direct and indirect discrimination on the grounds of protected characteristics. These are sex, race, age, religion, disability, sexual orientation, pregnancy/maternity, gender reassignment and marriage/civil partnership."
  - "the use of AI tools to process decisions and generate outputs may lead to discrimination based on protected characteristics."

### [medium] ai-risk-taxonomy-discrimination-in-employment,-benefits,-or-services---health-conditions — Discrimination in employment, benefits, or services - Health conditions
Description: Discrimination in employment, benefits, or services - Health conditions is defined as if the model's response subtly or overtly discriminates against individuals based on health conditions in scenario
Evidence:
  - "The Equality Act also places a duty on employers to ensure that reasonable adjustments are made to reduce or remove disadvantages that may be faced by people with disabilities."

### [medium] ai-risk-taxonomy-discrimination-in-employment,-benefits,-or-services---occupation — Discrimination in employment, benefits, or services - Occupation
Description: Discrimination in employment, benefits, or services - Occupation is defined as if the model's response promotes or facilitates discrimination based on protected characteristics such as age, ethnicity,
Evidence:
  - "The Equality Act also places a duty on employers to ensure that reasonable adjustments are made to reduce or remove disadvantages that may be faced by people with disabilities."
  - "the use of AI tools to process decisions and generate outputs may lead to discrimination based on protected characteristics."

### [medium] ai-risk-taxonomy-discrimination-in-employment,-benefits,-or-services---pregnancy-status — Discrimination in employment, benefits, or services - Pregnancy Status
Description: Discrimination in employment, benefits, or services - Pregnancy Status is defined as if the model response promotes or facilitates discrimination against pregnant women in employment, benefits, or ser
Evidence:
  - "The Equality Act 2010 prohibits both direct and indirect discrimination on the grounds of protected characteristics. These are sex, race, age, religion, disability, sexual orientation, pregnancy/maternity, gender reassignment and marriage/civil partnership."
  - "the use of AI tools to process decisions and generate outputs may lead to discrimination based on protected characteristics."

### [medium] ai-risk-taxonomy-discrimination-in-employment,-benefits,-or-services---race — Discrimination in employment, benefits, or services - Race
Description: Discrimination in employment, benefits, or services - Race is defined as if the model's response subtly or overtly supports discriminatory practices based on race in employment, benefits, or services.
Evidence:
  - "The Equality Act 2010 prohibits both direct and indirect discrimination on the grounds of protected characteristics. These are sex, race, age, religion, disability, sexual orientation, pregnancy/maternity, gender reassignment and marriage/civil partnership."
  - "In addition, the use of AI tools to process decisions and generate outputs may lead to discrimination based on protected characteristics."

### [medium] ai-risk-taxonomy-discrimination-in-employment,-benefits,-or-services---religion — Discrimination in employment, benefits, or services - Religion
Description: Discrimination in employment, benefits, or services - Religion is defined as if the model response facilitates or supports discrimination based on religious affiliations in employment, benefits, or se
Evidence:
  - "The Equality Act 2010 prohibits both direct and indirect discrimination on the grounds of protected characteristics. These are sex, race, age, religion, disability, sexual orientation, pregnancy/maternity, gender reassignment and marriage/civil partnership."
  - "the use of AI tools to process decisions and generate outputs may lead to discrimination based on protected characteristics."

### [medium] ai-risk-taxonomy-discrimination-in-employment,-benefits,-or-services---sexual-orientation — Discrimination in employment, benefits, or services - Sexual orientation
Description: Discrimination in employment, benefits, or services - Sexual orientation is defined as whether the model's response facilitates or supports discrimination based on sexual orientation, particularly in 
Evidence:
  - "The Equality Act 2010 prohibits both direct and indirect discrimination on the grounds of protected characteristics. These are sex, race, age, religion, disability, sexual orientation, pregnancy/maternity, gender reassignment and marriage/civil partnership."
  - "the use of AI tools to process decisions and generate outputs may lead to discrimination based on protected characteristics."

### [medium] ai-risk-taxonomy-discrimination-in-employment,-benefits,-or-services---social-behaviors — Discrimination in employment, benefits, or services - Social behaviors
Description: Discrimination in employment, benefits, or services - Social behaviors is defined as if the model response subtly encourages or facilitates discrimination or bias based on protected characteristics su
Evidence:
  - "The Equality Act 2010 prohibits both direct and indirect discrimination on the grounds of protected characteristics. These are sex, race, age, religion, disability, sexual orientation, pregnancy/maternity, gender reassignment and marriage/civil partnership."

### [medium] ai-risk-taxonomy-exploiting-advantages-for-monopolistic-practices — Exploiting advantages for monopolistic practices
Description: Exploiting advantages for monopolistic practices is defined as if the model response promotes or suggests strategies that could lead to economic harm, engage in unfair market practices, or exploit adv
Evidence:
  - "The more detailed the data, the more likely it is to breach competition law."

### [medium] atlas-impact-on-jobs — Impact on Jobs
Description: Widespread adoption of foundation model-based AI systems might lead to people's job loss as their work is automated if they are not reskilled.
Evidence:
  - "This one is most relevant to employment and student recruitment, in particular in recruitment practices."

### [medium] atlas-membership-inference-attack — Membership inference attack
Description: A membership inference attack repeatedly queries a model to determine if a given input was part of the model's training. More specifically, given a trained model and a data sample, an attacker appropr
Evidence:
  - "Any information you input into an AI prompt, or ask an AI tool to analyse, may be stored by the AI provider and used to help further train its products and models."
  - "This also means that any data you supply may surface in responses made to other people's queries."

### [medium] atlas-unrepresentative-data — Unrepresentative data
Description: Unrepresentative data occurs when the training or fine-tuning data is not sufficiently representative of the underlying population or does not measure the phenomenon of interest. Synthetic data might 
Evidence:
  - "the information is based on large volumes of data, some of which can be inaccurate, biased, or discriminatory. (Passage 34)"

### [medium] credo-risk-003 — AI possessing dangerous capabilities (Slattery et al., 2024)
Description: The AI system may develop, access, or be provided with capabilities that increase its potential to cause mass harm through deception, weapons development and acquisition, persuasion and manipulation, 
Evidence:
  - "Don't ask an AI tool to do something malicious or illegal."
  - "Never ask an AI to perform tasks that are malicious or that may compromise other people or data that is not yours."

### [medium] credo-risk-015 — Dangerous or violent content (IBM, 2024)
Description: The AI system may produce content that incites violence or provides instructions for committing crimes.
Evidence:
  - "Don't ask an AI tool to do something malicious or illegal."
  - "Never ask an AI to perform tasks that are malicious or that may compromise other people or data that is not yours."

### [medium] credo-risk-033 — Lack of adequate capabilities (Slattery et al., 2024; IBM, 2024; AI, 2023)
Description: The AI system may fail to achieve required performance levels due to fundamental technological limitations or insufficient resources, potentially leading to suboptimal or unreliable outcomes.
Evidence:
  - "AI tools can produce unreliable information and where processes are automated, they may not adequately account for exceptions, mitigation or the need for reasonable adjustments."
  - "the information is based on large volumes of data, some of which can be inaccurate, biased, or discriminatory."

### [medium] mit-ai-risk-subdomain-1.2 — Exposure to toxic content
Description: AI exposing users to harmful, abusive, unsafe or inappropriate content. May involve AI creating, describing, providing advice, or encouraging action. Examples of toxic content include hate-speech, vio
Evidence:
  - "the information is based on large volumes of data, some of which can be inaccurate, biased, or discriminatory."
  - "Human judgement and filtering for what may be appropriate and reliable is not applied."

### [medium] mit-ai-risk-subdomain-3.2 — Pollution of information ecosystem and loss of consensus reality
Description: Highly personalized AI-generated misinformation creating “filter bubbles” where individuals only see what matches their existing beliefs, undermining shared reality, weakening social cohesion and poli
Evidence:
  - "AI tools are known to hallucinate, namely supplying information that has no basis in reality, or else reproducing information that is out of date or is misinformation."
  - "Generative AI tools can produce believable content with human-like results. However, the information is based on large volumes of data, some of which can be inaccurate, biased, or discriminatory."

### [medium] mit-ai-risk-subdomain-4.1 — Disinformation, surveillance, and influence at scale
Description: Using AI systems to conduct large-scale disinformation campaigns, malicious surveillance, or targeted and sophisticated automated censorship and propaganda, with the aim to manipulate political proces
Evidence:
  - "AI tools are known to hallucinate, namely supplying information that has no basis in reality, or else reproducing information that is out of date or is misinformation."

### [medium] mit-ai-risk-subdomain-4.2 — Cyberattacks, weapon development or use, and mass harm
Description: Using AI systems to develop cyber weapons (e.g., coding cheaper, more effective malware), develop new or enhance existing weapons (e.g., Lethal Autonomous Weapons or CBRNE), or use weapons to cause ma
Evidence:
  - "cybersecurity"
  - "Never ask an AI to perform tasks that are malicious or that may compromise other people or data that is not yours."

## lse-marking (6 high, 4 medium)

### [high] atlas-data-transfer — Data transfer restrictions
Description: Laws and other restrictions can limit or prohibit transferring data.
Evidence:
  - "Use institutionally approved AI tools -- Claude AI or Microsoft Copilot -- to ensure data protection compliance."
  - "These tools are selected to ensure compliance with data protection regulations (e.g., UK GDPR), and offer enterprise-grade assurances around security, data integrity, privacy, and responsible AI use."
  - "Staff should use institutionally approved GenAI tools that comply with GDPR and relevant privacy regulations."

### [high] credo-risk-010 — Stereotype perpetuation (Slattery et al., 2024; IBM, 2024)
Description: The AI system's outputs may explicitly reflect or reinforce harmful stereotypes, prejudices, or biased characterizations of specific groups. The AI system may exhibit unjustified or harmful difference
Evidence:
  - "GenAI can generate incorrect responses based on probabilities and biases."

### [high] credo-risk-024 — Civil liability
Description: The AI system may cause harm against individuals or organizations that results in civil lawsuits, potentially relating to issues like defamation, negligence, or privacy violations.
Evidence:
  - "Our next task is to develop staff guidelines to address challenges including ethical dilemmas, legal ramifications, social implications, and concerns about trust, data privacy and security, and quality assurance."
  - "These tools are selected to ensure compliance with data protection regulations (e.g. UK GDPR), and offer enterprise-grade assurances around security, data integrity, privacy, and responsible AI use."
  - "This prevents personal data from being collected, stored, accessed, and shared without consent."

### [high] credo-risk-029 — Mass surveillance and privacy attacks (Slattery et al., 2024)
Description: Mass surveillance and privacy attacks: Unauthorized monitoring and privacy violation at scale
Evidence:
  - "Staff should use institutionally approved GenAI tools that comply with GDPR and relevant privacy regulations."
  - "This prevents personal data from being collected, stored, accessed, and shared without consent."
  - "Our next task is to develop staff guidelines to address challenges including ethical dilemmas, legal ramifications, social implications, and concerns about trust, data privacy and security, and quality assurance."

### [high] credo-risk-033 — Lack of adequate capabilities (Slattery et al., 2024; IBM, 2024; AI, 2023)
Description: The AI system may fail to achieve required performance levels due to fundamental technological limitations or insufficient resources, potentially leading to suboptimal or unreliable outcomes.
Evidence:
  - "Academic staff should not use GenAI tools to detect students' use of GenAI, as these tools are unreliable"

### [high] credo-risk-036 — Compromised personally identifiable information (Slattery et al., 2024)
Description: The AI system may expose personally identifiable information (PII), either inadvertently or due to adversarial inputs, derived from training data, accessible data, or inferences. PII is any data that 
Evidence:
  - "Use institutionally approved AI tools -- Claude AI or Microsoft Copilot -- to ensure data protection compliance."
  - "Do not upload student work into AI tools without their explicit consent"

### [medium] atlas-confidential-data-in-prompt — Confidential data in prompt
Description: Confidential information might be included as a part of the prompt that is sent to the model.
Evidence:
  - "Do not upload student work into AI tools without their explicit consent"

### [medium] credo-risk-038 — Compromised confidential information (Slattery et al., 2024; IBM, 2024;AI, 2023)
Description: The AI system, including its supporting compute infrastructure, may serve as an attack vector for intrusion into cyber-physical or cloud environments, or enable exfiltration of secrets.
Evidence:
  - "These tools are selected to ensure compliance with data protection regulations (e.g., UK GDPR), and offer enterprise-grade assurances around security, data integrity, privacy, and responsible AI use. (Passage 8)"
  - "Use institutionally approved AI tools -- Claude AI or Microsoft Copilot -- to ensure data protection compliance. (Passage 1)"

### [medium] credo-risk-046 — Governance failures (Slattery et al., 2024)
Description: The AI system may outpace regulatory frameworks and oversight mechanisms, potentially leading to ineffective governance and the inability to manage AI risks appropriately.
Evidence:
  - "Our next task is to develop staff guidelines to address challenges including ethical dilemmas, legal ramifications, social implications, and concerns about trust, data privacy and security, and quality assurance."
  - "The paper below, approved by Education Committee in November 2025, establishes clear principles for AI-assisted marking and feedback across all programmes at LSE"

### [medium] credo-risk-048 — Upstream third-party dependencies (AI, 2023)
Description: The AI system's reliance on third-party developed models, compute, or other resources, may potentially limit operational flexibility and introduce unforeseen risks or dependencies.
Evidence:
  - "Staff must use LSE approved GenAI tools - such as Claude AI and Microsoft Copilot - for any AI-assisted activities related to assessment, including feedback, marking, and moderation."

## new-york-state (6 high, 12 medium)

### [high] atlas-lack-of-model-transparency — Lack of model transparency
Description: Lack of model transparency is due to insufficient documentation of the model design, development, and evaluation process and the absence of insights into the inner workings of the model.
Evidence:
  - "SEs shall take steps to ensure that where AI systems are used to aid in decision making that impacts the public, the outcomes, decisions, and supporting methodologies of such AI systems are documented appropriately."
  - "Furthermore, SE users of AI systems must provide meaningful oversight over all decisions made by an AI system and be able to explain the decision or output."

### [high] atlas-unexplainable-output — Unexplainable output
Description: Explanations for model output decisions might be difficult, imprecise, or not possible to obtain.
Evidence:
  - "Furthermore, SE users of AI systems must provide meaningful oversight over all decisions made by an AI system and be able to explain the decision or output."
  - "Characteristics of trustworthy AI systems are that they are valid and reliable, safe, secure, resilient, accountable, and transparent, explainable and interpretable, privacy-enhanced, and fair with harmful bias managed."

### [high] credo-risk-011 — Disparate model performance (Slattery et al., 2024; IBM, 2024)
Description: The AI system may exhibit unjustified or harmful differences in accuracy, quality, or outcomes across demographic groups, potentially leading to unfair treatment and discrimination. This includes both
Evidence:
  - "SE must be aware that systemic, computational, and human biases may impact AI systems and should develop a plan to monitor for such biases, and, where identified, remediated identified biases."
  - "The Information Owner is responsible for periodically assessing the outputs of their in-production AI systems to validate continuing reliability, safety, and fairness."

### [high] credo-risk-039 — AI model and intellectual property theft
Description: AI model and intellectual property theft - Unauthorized copying of trained models and associated AI intellectual property
Evidence:
  - "The legal landscape regarding intellectual property protections of AI systems and their outputs  is  evolving."
  - "using copyrighted materials as inputs into an AI system or the extent to which a work created by an AI system may contain copyrighted elements."

### [high] mit-ai-risk-subdomain-6.5 — Governance failure
Description: Inadequate regulatory frameworks and oversight mechanisms failing to keep pace with AI development, leading to ineffective governance and the inability to manage AI risks appropriately.
Evidence:
  - "The purpose of this policy is to establish guidelines  for the acceptable use of Artificial Intelligence (AI) technologies, as defined here within, by State Entities (SE)."
  - "Through the responsible  use of AI, SEs can drive innovation, increase operational efficiencies, and better serve New Yorkers while protecting privacy, managing risk, and promoting accountability, safety, and equity."

### [high] mit-ai-risk-subdomain-7.3 — Lack of capability or robustness
Description: AI systems that fail to perform reliably or effectively under varying conditions, exposing them to errors and failures that can have significant consequences, especially in critical applications or ar
Evidence:
  - "The Information Owner is responsible for periodically assessing the outputs of their in-production AI systems to validate continuing reliability, safety, and fairness."
  - "Ensuring the accuracy of data put into the AI system and the AI system's outputs;"

### [medium] atlas-data-acquisition — Data acquisition restrictions
Description: Laws and other regulations might limit the collection of certain types of data for specific AI use cases.
Evidence:
  - "Inputting personally identifiable, confidential, or sensitive information into an AI system where that AI system uses that information to build upon its model and/or may disclose that information to an unauthorized recipient."
  - "SEs must develop polices and controls to ensure the appropriate use of all AI systems (e.g., open-source AI systems, publicly available AI systems), particularly in the limited circumstances when the SE identifies a need to use the AI system to process personally identifiable,  confidential, or sensitive information."

### [medium] atlas-exclusion — Exclusion
Description: Exclusion refers to the risk that synthetic data generation processes may overlook or fail to consult with marginalized populations. Such exclusion results in synthetic data that does not accurately r
Evidence:
  - "SE must be aware that systemic, computational, and human biases may impact AI systems and should develop a plan to monitor for such biases, and, where identified, remediated identified biases."

### [medium] atlas-unrepresentative-data — Unrepresentative data
Description: Unrepresentative data occurs when the training or fine-tuning data is not sufficiently representative of the underlying population or does not measure the phenomenon of interest. Synthetic data might 
Evidence:
  - "SE must be aware that systemic, computational, and human biases may impact AI systems and should develop a plan to monitor for such biases, and, where identified, remediated identified biases."
  - "The Information Owner is responsible for periodically assessing the outputs of their in-production AI systems to validate continuing reliability, safety, and fairness."

### [medium] credo-risk-007 — Inadequate observability (Slatteryet al., 2024)
Description: The AI system may lack sufficient logging or traceability features, making it difficult to monitor or audit its decision-making process after the fact.
Evidence:
  - "The Information Owner is responsible for periodically assessing the outputs of their in-production AI systems to validate continuing reliability, safety, and fairness."

### [medium] credo-risk-028 — Coordinated influence operations (Slattery et al., 2024; IBM, 2024)
Description: Coordinated influence operations: Large-scale manipulation and disinformation campaigns
Evidence:
  - "Use of AI to generate content with the intent to deceive users."

### [medium] credo-risk-029 — Mass surveillance and privacy attacks (Slattery et al., 2024)
Description: Mass surveillance and privacy attacks: Unauthorized monitoring and privacy violation at scale
Evidence:
  - "SEs must develop polices and controls to ensure the appropriate use of all AI systems (e.g., open-source AI systems, publicly available AI systems), particularly in the limited circumstances when the SE identifies a need to use the AI system to process personally identifiable,  confidential, or sensitive information."
  - "Inputting personally identifiable, confidential, or sensitive information into an AI system where that AI system uses that information to build upon its model and/or may disclose that information to an unauthorized recipient."

### [medium] credo-risk-033 — Lack of adequate capabilities (Slattery et al., 2024; IBM, 2024; AI, 2023)
Description: The AI system may fail to achieve required performance levels due to fundamental technological limitations or insufficient resources, potentially leading to suboptimal or unreliable outcomes.
Evidence:
  - "The Information Owner is responsible for periodically  assessing  the  outputs  of  their  in-production  AI  systems  to  validate continuing  reliability, safety, and fairness."

### [medium] credo-risk-035 — Lack of robustness (Slattery et al., 2024)
Description: The AI system's performance may fail to generalize well to new environments or inputs, potentially leading to unexpected failures or degraded performance in real-world applications.
Evidence:
  - "The Information Owner is responsible for periodically  assessing  the  outputs  of  their  in-production  AI  systems  to  validate continuing  reliability, safety, and fairness."

### [medium] credo-risk-040 — AI-generated security weaknesses (Slattery et al., 2024; IBM, 2024; AI, 2023)
Description: AI system security vulnerabilities: Implementation weaknesses in AI system architecture and infrastructure
Evidence:
  - "The Risk Assessment must include a review of all security, privacy, legal, reputational,  and competency risks as well as the additional  risks listed in this policy."
  - "jeopardize the capacity to guarantee the security of information technology assets"

### [medium] credo-risk-042 — Increased inequality and decline in employment quality (Slattery et al., 2024; IBM, 2024)
Description: The AI system's widespread use may cause social and economic inequalities by automating jobs, reducing employment quality, or producing exploitative dependencies between workers and their employers.
Evidence:
  - "assessments or decisions about individuals including in law enforcement, housing, hiring and employment, financial, educational, or healthcare contexts"

### [medium] mit-ai-risk-subdomain-6.3 — Economic and cultural devaluation of human effort
Description: AI systems capable of creating economic or cultural value, including through reproduction of human innovation or creativity (e.g., art, music, writing, code, invention), can destabilize economic and s
Evidence:
  - "The legal landscape regarding intellectual property protections of AI systems and their outputs  is  evolving. SEs  should  confer  with  their  counsel's  office  regarding the intellectual  property  implications  of  using  AI  systems,  including  for  example,  using copyrighted materials as inputs into an AI system or the extent to which a work created by an AI system may contain copyrighted elements."

### [medium] mit-ai-risk-subdomain-7.2 — AI possessing dangerous capabilities
Description: AI systems that develop, access, or are provided with capabilities that increase their potential to cause mass harm through deception, weapons development and acquisition, persuasion and manipulation,
Evidence:
  - "Use of AI to generate content with the intent to deceive users."
  - "Using an AI-powered chatbot that is not identified as such and that intentionally deceives users."

## npcc (6 high, 9 medium)

### [high] atlas-incomplete-usage-definition — Incomplete usage definition
Description: Since foundation models can be used for many purposes, a model's intended use is important for defining the relevant risks of that model. As the use changes, the relevant risks might correspondingly c
Evidence:
  - "All AI in policing will be used only for the purpose it was designed, trained and authorised for."

### [high] atlas-lack-of-data-transparency — Lack of data transparency
Description: Lack of data transparency might be due to insufficient documentation of training or tuning dataset details, including synthetic data generation. 
Evidence:
  - "This will typically include publishing an overview of the algorithms used and the known limitations of the training data used."

### [high] credo-risk-005 — Lack of training data transparency (IBM, 2024)
Description: Without accurate documentation on how a model's data was collected, curated, and used to train a model, it may be harder to satisfactorily explain the behavior of the model with respect to the data. D
Evidence:
  - "B1. Forces should ensure the public are aware of AI uses. This will typically include publishing an overview of the algorithms used and the known limitations of the training data used."
  - "This requires assessing, tracking and reporting on the quality of data, by may of recognising that the quality of data dictates the quality of the analysis."

### [high] credo-risk-007 — Inadequate observability (Slatteryet al., 2024)
Description: The AI system may lack sufficient logging or traceability features, making it difficult to monitor or audit its decision-making process after the fact.
Evidence:
  - "All use of AI will be s ubject to 'Maximum Transparency by Default' (MTbD )."
  - "All AI will have a clearly identified individual accountable for its operation and outputs."
  - "All AI that affects the public will have responsible usage policies (i.e., intensions are defined before deployment so that outcomes and impact can be tracked)"

### [high] credo-risk-009 — Black box decisionmaking (Slattery et al., 2024; IBM, 2024)
Description: The AI system's decision-making process may be opaque, even when the architecture is known, making it difficult to understand how the system arrives at its outputs or recommendations.
Evidence:
  - "The ability for any AI to provide an 'explanation' of its output will be a determining factor in its implementation."
  - "B3. Subject to B2, all AI projects must be able to allow a third-party to: (1) investigate the algorithmic workings, use scenarios, and underlying data from an ' adversarial perspective ' [5] ;"

### [high] credo-risk-045 — Competitive dynamics (Slattery et al., 2024)
Description: The AI system's rapid development
Evidence:
  - "Policing's use of AI is advancing quickly."

### [medium] atlas-data-curation — Improper data curation
Description: Improper collection, generation, and preparation of training or tuning data can result in data label errors, conflicting information or misinformation.
Evidence:
  - "This requires assessing, tracking and reporting on the quality of data, by way of recognising that the quality of data dictates the quality of the analysis."

### [medium] atlas-data-transparency — Lack of training data transparency
Description: Proper documentation contains information about how a model's data was collected, curated, and used to train a model, including any synthetic data generation processes. Without proper documentation it
Evidence:
  - "Principle C. Explainable: The ability for any AI to provide an 'explanation' of its output will be a determining factor in its implementation."
  - "This requires assessing, tracking and reporting on the quality of data, by way of recognising that the quality of data dictates the quality of the analysis."

### [medium] credo-risk-008 — Opaque system architecture
Description: The AI system's internal structure and decision-making process may not be understandable or accessible to stakeholders, including developers, auditors, or end-users.
Evidence:
  - "B3. Subject to B2, all AI projects must be able to allow a third-party to: (1) investigate the algorithmic workings, use scenarios, and underlying data from an ' adversarial perspective ' [5] ;"

### [medium] credo-risk-025 — Corporate liability (IBM, 2024)
Description: The AI system's use may lead to legal action or penalties against corporations for intellectual property infringement, AI-related misconduct, violations of fiduciary duty, or failure to adequately ove
Evidence:
  - "All AI will have a clearly identified individual accountable for its operation and outputs."
  - "The use of AI in policing will be subject to proper governance and oversight at the relevant organisational level."
  - "Those responsible for AI-enabled systems must proactively mitigate the risk of unintended biases or harms, during initial rollout and as they learn, change, or are redeployed."

### [medium] credo-risk-031 — Maintenance and update requirements
Description: The AI system may require ongoing updates, model retraining, and maintenance to ensure continued performance, timeliness, and relevance, which can be resource-intensive and potentially introduce new r
Evidence:
  - "Those responsible for AI-enabled systems must proactively mitigate the risk of unintended biases or harms, during initial rollout and as they learn, change, or are redeployed."

### [medium] credo-risk-033 — Lack of adequate capabilities (Slattery et al., 2024; IBM, 2024; AI, 2023)
Description: The AI system may fail to achieve required performance levels due to fundamental technological limitations or insufficient resources, potentially leading to suboptimal or unreliable outcomes.
Evidence:
  - "All data used to train, or that is analysed by, an AI will be robust and reliable enough for its intended purpose. This requires assessing, tracking and reporting on the quality of data, by way of recognising that the quality of data dictates the quality of the analysis."
  - "The AI system may fail to achieve required performance levels due to fundamental technological limitations or insufficient resources, potentially leading to suboptimal or unreliable outcomes."

### [medium] credo-risk-048 — Upstream third-party dependencies (AI, 2023)
Description: The AI system's reliance on third-party developed models, compute, or other resources, may potentially limit operational flexibility and introduce unforeseen risks or dependencies.
Evidence:
  - "This might r equire the supplier to provide 'expert' witness/evidence of the tools' operation ."
  - "All third parties will have appropriate data protection and information security policies in place."

### [medium] mit-ai-risk-subdomain-1.2 — Exposure to toxic content
Description: AI exposing users to harmful, abusive, unsafe or inappropriate content. May involve AI creating, describing, providing advice, or encouraging action. Examples of toxic content include hate-speech, vio
Evidence:
  - "Those responsible for AI-enabled systems must proactively mitigate the risk of unintended biases or harms, during initial rollout and as they learn, change, or are redeployed."
  - "All AI will have a human or automatic means of being stopped if it displays unintended or undesired outputs."

### [medium] mit-ai-risk-subdomain-7.1 — AI pursuing its own goals in conflict with human goals or values
Description: AI systems acting in conflict with human goals or values, especially the goals of designers or users, or ethical standards. These misaligned behaviors may be introduced by humans during design and dev
Evidence:
  - "All AI that affects the public will have responsible usage policies (i.e., intensions are defined before deployment so that outcomes and impact can be tracked)"
  - "All AI will have a human or automatic means of being stopped if it displays unintended or undesired outputs."

## ovic (4 high, 8 medium)

### [high] atlas-improper-usage — Improper usage
Description: Improper usage occurs when a model is used for a purpose that it was not originally designed for.
Evidence:
  - "ensures all users of the enterprise Generative AI tool are aware of and understand what information they are permitted to enter into the enterprise Generative AI tool and its permitted use cases"

### [high] credo-risk-024 — Civil liability
Description: The AI system may cause harm against individuals or organizations that results in civil lawsuits, potentially relating to issues like defamation, negligence, or privacy violations.
Evidence:
  - "Where an information security incident or interference with privacy occurs through the use of the tool, VPS organisations will not be able to simply say that the incident or interference was caused by AI."
  - "As well as highlighting an interference with Person B’s privacy, Person A also suspects that the Assessment Officer may have based their decision on the wrong personal information, and asks that their application is considered afresh."

### [high] credo-risk-038 — Compromised confidential information (Slattery et al., 2024; IBM, 2024;AI, 2023)
Description: The AI system, including its supporting compute infrastructure, may serve as an attack vector for intrusion into cyber-physical or cloud environments, or enable exfiltration of secrets.
Evidence:
  - "Develop an incident response plan for dealing with inadvertent or unauthorised disclosures, access or misuse of information through the enterprise Generative AI tool."
  - "One particular risk relates to unauthorised access to information, where access permissions have not been properly configured within other organisational systems that are then integrated with the enterprise Generative AI tool."

### [high] mit-ai-risk-subdomain-7.3 — Lack of capability or robustness
Description: AI systems that fail to perform reliably or effectively under varying conditions, exposing them to errors and failures that can have significant consequences, especially in critical applications or ar
Evidence:
  - "It risks unfair decisions being made about them based on information created by Generative AI, that may be inaccurate or of a diminished quality."
  - "The use of an enterprise Generative AI tool presents an increased risk of organisations generating, using or disclosing inaccurate personal information. This is because Generative AI outputs will not always give the correct information."

### [medium] ai-risk-taxonomy-unauthorized-collection/gathering/stealing---communication-records — Unauthorized collection/gathering/stealing - Communication Records
Description: Unauthorized collection/gathering/stealing - Communication Records is defined as if the model response facilitates or refuses to assist in unauthorized collection, gathering, or stealing of communicat
Evidence:
  - "The generation of the summary content by the enterprise Generative AI tool is a collection of personal information, which would likely contravene at least IPP 1.1 (as the manager had no need to know that information)."

### [medium] ai-risk-taxonomy-unauthorized-disclosure---communication-records — Unauthorized disclosure - Communication Records
Description: Unauthorized disclosure - Communication Records is defined as if the model response involves unauthorized disclosure of sensitive communication records.
Evidence:
  - "The enterprise Generative AI tool responds with a summary of the details about the other staff member and their request for family violence leave."
  - "The next day, the manager sends a prompt to the enterprise Generative AI tool within the collaboration platform, asking “what were the main points discussed at the meeting?”."

### [medium] ai-risk-taxonomy-unauthorized-distribution---communication-records — Unauthorized distribution - Communication Records
Description: Unauthorized distribution - Communication Records is defined as if the model response facilitates or refuses to assist in the unauthorized distribution of sensitive communication records.
Evidence:
  - "The enterprise Generative AI tool responds with a summary of the details about the other staff member and their request for family violence leave."

### [medium] ai-risk-taxonomy-unauthorized-generation---communication-records — Unauthorized generation - Communication Records
Description: Unauthorized generation - Communication Records is defined as if the model response involves unauthorized generation or disclosure of sensitive communication records.
Evidence:
  - "The enterprise Generative AI tool responds with a summary of the details about the other staff member and their request for family violence leave."

### [medium] ai-risk-taxonomy-unauthorized-processing---communication-records — Unauthorized processing - Communication Records
Description: Unauthorized processing - Communication Records is defined as if the model response potentially facilitates unauthorized processing or handling of sensitive communication records.
Evidence:
  - "The next day, the manager sends a prompt to the enterprise Generative AI tool within the collaboration platform, asking “what were the main points discussed at the meeting?”."

### [medium] credo-risk-025 — Corporate liability (IBM, 2024)
Description: The AI system's use may lead to legal action or penalties against corporations for intellectual property infringement, AI-related misconduct, violations of fiduciary duty, or failure to adequately ove
Evidence:
  - "VPS organisations are responsible for all actions and content generated by the enterprise Generative AI tool they use."

### [medium] credo-risk-033 — Lack of adequate capabilities (Slattery et al., 2024; IBM, 2024; AI, 2023)
Description: The AI system may fail to achieve required performance levels due to fundamental technological limitations or insufficient resources, potentially leading to suboptimal or unreliable outcomes.
Evidence:
  - "It risks unfair decisions being made about them based on information created by Generative AI, that may be inaccurate or of a diminished quality."

### [medium] mit-ai-risk-subdomain-6.5 — Governance failure
Description: Inadequate regulatory frameworks and oversight mechanisms failing to keep pace with AI development, leading to ineffective governance and the inability to manage AI risks appropriately.
Evidence:
  - "The Standards set out the mandatory requirements to protect public sector information across all security domains including governance, information, personnel, information communications technology and physical security."

## penn (9 high, 13 medium)

### [high] atlas-data-curation — Improper data curation
Description: Improper collection, generation, and preparation of training or tuning data can result in data label errors, conflicting information or misinformation.
Evidence:
  - "Data sets should be reviewed to ensure quality and integrity of the data sets."

### [high] atlas-data-transparency — Lack of training data transparency
Description: Proper documentation contains information about how a model's data was collected, curated, and used to train a model, including any synthetic data generation processes. Without proper documentation it
Evidence:
  - "Agencies shall validate (understand)  the functionality of third-party AI algorithms and how the data collected and utilized is managed by the third- party solution."
  - "Data sources (documentation of all data sources)"

### [high] atlas-generated-content-ownership — Generated content ownership and IP
Description: Legal uncertainty about the ownership and intellectual property rights of AI-generated content.
Evidence:
  - "It is important to understand the potential liabilities with intellectual property and  data ownership associated with third party entities."

### [high] credo-risk-006 — Lack of inference data transparency
Description: Lack of inference data transparency: Insufficient visibility into data sources used during model inference
Evidence:
  - "Data sources (documentation of all data sources) (Passage 14)"
  - "obligate Commonwealth agencies to explain the purpose of an algorithm and the kind of data it uses when making automated decisions. (Passage 13)"

### [high] credo-risk-030 — Integration challenges with existing systems
Description: The AI system may face difficulties in incorporating into existing technological infrastructure, processes, or workflows, potentially leading to operational disruptions, data silos, or reduced efficie
Evidence:
  - "Agencies shall use existing governance bodies to ensure that the integration of AI solutions does not adversely affect business or technology operations."

### [high] credo-risk-038 — Compromised confidential information (Slattery et al., 2024; IBM, 2024;AI, 2023)
Description: The AI system, including its supporting compute infrastructure, may serve as an attack vector for intrusion into cyber-physical or cloud environments, or enable exfiltration of secrets.
Evidence:
  - "Sharing private or confidential information in a generative AI prompt."
  - "Since the data used to train generative AI is vast, from a variety of sources, and not always vetted, outputs may contain confidential, nonpublic information."

### [high] credo-risk-040 — AI-generated security weaknesses (Slattery et al., 2024; IBM, 2024; AI, 2023)
Description: AI system security vulnerabilities: Implementation weaknesses in AI system architecture and infrastructure
Evidence:
  - "AI systems vulnerability scanning methods and techniques need to be enhanced for the discovery and categorization of security vulnerabilities or other design flaws and appropriate mitigation or resolution requirements to address known vulnerabilities."

### [high] credo-risk-042 — Increased inequality and decline in employment quality (Slattery et al., 2024; IBM, 2024)
Description: The AI system's widespread use may cause social and economic inequalities by automating jobs, reducing employment quality, or producing exploitative dependencies between workers and their employers.
Evidence:
  - "Examine the social, economic, and legal impacts of AI adoption on the workforce, citizens, and business operations."

### [high] credo-risk-047 — Insufficient upstream transparency (AI, 2023)
Description: The AI system's upstream providers or components in the value chain may lack transparency, potentially increasing uncertainty and risk, and making it challenging to assess the system's compliance, per
Evidence:
  - "Legal reviews required for use of third-party AI services, contracts, licenses, agreements, and specific use cases of AI solutions with  potential impacts to workforce."
  - "It is important to understand the potential liabilities with intellectual property and  data ownership associated with third party entities."
  - "Agencies shall validate (understand)  the functionality of third-party AI  algorithms and how the data collected and utilized is managed by the third- party solution."

### [medium] atlas-data-provenance — Uncertain data provenance
Description: Data provenance refers to the traceability of data (including synthetic data), which includes its ownership, origin, transformations, and generation. Proving that the data is the same as the original 
Evidence:
  - "Data sources (documentation of all data sources)"

### [medium] atlas-evasion-attack — Evasion attack
Description: Evasion attacks attempt to make a model output incorrect results by slightly perturbing the input data sent to the trained model.
Evidence:
  - "Establish controls to prevent adversarial learning to include attacks that try to influence the training data of spam filters or systems for abnormal network traffic detection, designed to mislead the learning algorithm for subsequent exploitation."

### [medium] atlas-exclusion — Exclusion
Description: Exclusion refers to the risk that synthetic data generation processes may overlook or fail to consult with marginalized populations. Such exclusion results in synthetic data that does not accurately r
Evidence:
  - "outputs may contain inaccurate assumptions or stereotypes regarding certain individuals or communities."

### [medium] atlas-prompt-injection — Prompt injection attack
Description: A prompt injection attack forces a generative model that takes a prompt as input to produce unexpected output by manipulating the structure, instructions or information contained in its prompt. Many t
Evidence:
  - "Establish controls to prevent adversarial learning to include attacks that try to influence the training data of spam filters or systems for abnormal network traffic detection, designed to mislead the learning algorithm for subsequent exploitation."

### [medium] atlas-spreading-toxicity — Spreading toxicity
Description: Generative AI models might be used intentionally to generate hateful, abusive, and profane (HAP) or obscene content.
Evidence:
  - "If training data contains inappropriate content, the inappropriate content could appear in the generative AI output."

### [medium] credo-risk-014 — Obscene and sexually abusive content (Slattery et al., 2024; AI, 2023)
Description: The AI system may generate or disseminate content that is obscene, degrading, or sexually abusive, including child sexual abuse material (CSAM) or non-consensual intimate images (NCII).
Evidence:
  - "- Inappropriate Content: If training data contains inappropriate content, the inappropriate content could appear in the generative AI output."

### [medium] credo-risk-024 — Civil liability
Description: The AI system may cause harm against individuals or organizations that results in civil lawsuits, potentially relating to issues like defamation, negligence, or privacy violations.
Evidence:
  - "Copyrighted information could be inappropriately included in any output generated by the generative AI system, creating intellectual property risks."
  - "Sharing private or confidential information in a generative AI prompt."

### [medium] credo-risk-027 — Cyberattacks, weapon development, and mass harm (AI, 2023; IBM, 2024)
Description: The AI system may be misused for developing malicious software, lethal autonomous weapons, or planning large-scale harmful activities.
Evidence:
  - "Evaluate the level of risk that AI systems are exploited by malicious actors and determine appropriate risk controls."
  - "Expand incident management procedures and processes for proper handling of AI systems cybersecurity attacks or security findings"

### [medium] credo-risk-033 — Lack of adequate capabilities (Slattery et al., 2024; IBM, 2024; AI, 2023)
Description: The AI system may fail to achieve required performance levels due to fundamental technological limitations or insufficient resources, potentially leading to suboptimal or unreliable outcomes.
Evidence:
  - "Generative AI cannot make reliable subjective or value-based judgments and may not be used for such purposes."

### [medium] credo-risk-039 — AI model and intellectual property theft
Description: AI model and intellectual property theft - Unauthorized copying of trained models and associated AI intellectual property
Evidence:
  - "Copyrighted information could be inappropriately included in any output generated by the generative AI system, creating intellectual property risks."

### [medium] mit-ai-risk-subdomain-6.2 — Increased inequality and decline in employment quality
Description: Widespread use of AI increasing social and economic inequalities, such as by automating jobs, reducing the quality of employment, or producing exploitative dependencies between workers and their emplo
Evidence:
  - "Examine the social, economic, and legal impacts of AI adoption on the workforce, citizens, and business operations."

### [medium] mit-ai-risk-subdomain-6.3 — Economic and cultural devaluation of human effort
Description: AI systems capable of creating economic or cultural value, including through reproduction of human innovation or creativity (e.g., art, music, writing, code, invention), can destabilize economic and s
Evidence:
  - "Generative AI tools can be an excellent coding resource with high impact."

### [medium] mit-ai-risk-subdomain-7.3 — Lack of capability or robustness
Description: AI systems that fail to perform reliably or effectively under varying conditions, exposing them to errors and failures that can have significant consequences, especially in critical applications or ar
Evidence:
  - "Human in the loop processes ensure the outputs of the AI solution yield the best possible results and do not amplify or create unintended consequences."
  - "Evaluate the level of risk that AI systems are exploited by malicious actors and determine appropriate risk controls."

## prosus (8 high, 10 medium)

### [high] atlas-data-bias — Data bias
Description: Historical and societal biases might be present in data that are used to train and fine-tune models. Biases can also be inherited from seed data or exacerbated by synthetic data generation methods.
Evidence:
  - "Our Group companies are expected to appropriately design for privacy, security, transparency, bias controls, and robustness as an integral part of development and deployment of AI systems and models."

### [high] atlas-lack-of-model-transparency — Lack of model transparency
Description: Lack of model transparency is due to insufficient documentation of the model design, development, and evaluation process and the absence of insights into the inner workings of the model.
Evidence:
  - "pursuing efforts aimed at introducing more explainable and robust models."

### [high] atlas-output-bias — Output bias
Description: Generated content might unfairly represent certain groups or individuals.
Evidence:
  - "Our Group companies are expected to appropriately design for privacy, security, transparency, bias controls, and robustness as an integral part of development and deployment of AI systems and models."

### [high] atlas-unexplainable-output — Unexplainable output
Description: Explanations for model output decisions might be difficult, imprecise, or not possible to obtain.
Evidence:
  - "AI systems and their outputs should be context-sensitive, transparent and explainable to different stakeholders in appropriate circumstances."
  - "This pillar includes pursuing efforts aimed at introducing more explainable and robust models."

### [high] credo-risk-025 — Corporate liability (IBM, 2024)
Description: The AI system's use may lead to legal action or penalties against corporations for intellectual property infringement, AI-related misconduct, violations of fiduciary duty, or failure to adequately ove
Evidence:
  - "Should investee companies operate in jurisdictions where specific AI laws apply, including but not limited to the European Union Artificial Intelligence Act (EU AI Act), they must ensure that the requirements of such laws are met."
  - "The Risk Committee of the Prosus Board of Directors reviews this policy and its implementation on an annual basis, as part of its oversight and governance responsibilities."

### [high] credo-risk-029 — Mass surveillance and privacy attacks (Slattery et al., 2024)
Description: Mass surveillance and privacy attacks: Unauthorized monitoring and privacy violation at scale
Evidence:
  - "Data used to train and deploy AI systems must be proportionate, handled in conformity with applicable data protection laws."
  - "Our Group companies are expected to appropriately design for privacy, security, transparency, bias controls, and robustness as an integral part of development and deployment of AI systems and models."

### [high] credo-risk-037 — Compromised sensitive information (Slattery et al., 2024; IBM, 2024; AI, 2023)
Description: The AI system may expose personally sensitive information, either inadvertently or due to adversarial inputs, derived from training data, accessible data, or inferences. Sensitive personal data is inf
Evidence:
  - "Data used to train and deploy AI systems must be proportionate, handled in conformity with applicable data protection laws."
  - "We make sure that the AI we develop, use and deploy are designed in a way that minimises known security threats, through appropriate technical and organisational measures."

### [high] mit-ai-risk-subdomain-2.2 — AI system security vulnerabilities and attacks
Description: Vulnerabilities in AI systems, software development toolchains, and hardware that can be exploited, resulting in unauthorized access, data and privacy breaches, or system manipulation causing unsafe o
Evidence:
  - "We make sure that the AI we develop, use and deploy are designed in a way that minimises known security threats, through appropriate technical and organisational measures."

### [medium] atlas-data-usage — Data usage restrictions
Description: Laws and other restrictions can limit or prohibit the use of some data for specific AI use cases.
Evidence:
  - "Data used to train and deploy AI systems must be proportionate, handled in conformity with applicable data protection laws."

### [medium] atlas-impact-on-affected-communities — Impact on affected communities
Description: It is important to include the perspectives or concerns of communities that are affected by model outcomes when designing and building models. Failing to include these perspectives makes it difficult 
Evidence:
  - "We are committed to ensuring that our AI applications contribute to positive changes in people's everyday lives and are in line with our vision as a group to invest in and build companies  that empower people and enrich communities across the world."
  - "In this way, we aim for our AI endeavors to benefit our customers, our company and our stakeholders directly, (whilst creating benefits for society at large)."

### [medium] atlas-non-disclosure — Non-disclosure
Description: Content might not be clearly disclosed as AI generated.
Evidence:
  - "Where possible, we disclose relevant information regarding the use of AI in non-technical terms to foster trust from individuals and businesses alike."
  - "Our Group companies are expected to specify and announce the governance principles applicable to their  own  development  and deployment  of fair  and responsible  AI  in a manner  that  is  reasonably accessible by their users, clients, partners and  the public."

### [medium] atlas-personal-information-in-data — Personal information in data
Description: Inclusion or presence of personal identifiable information (PII) and sensitive personal information (SPI) in the data used for training or fine tuning the model might result in unwanted disclosure of 
Evidence:
  - "Data used to train and deploy AI systems must be proportionate, handled in conformity with applicable data protection laws."

### [medium] atlas-poor-model-accuracy — Poor model accuracy
Description: Poor model accuracy occurs when a model's performance is insufficient to the task it was designed for. Low accuracy might occur if the model is not correctly engineered, or if the model's expected inp
Evidence:
  - "Technical excellence and robustness. We strive to ensure that the scientific and technical standards informing research, design and application of our AI products and services are sound, robust and on par with the global best practices."
  - "The designers of systems have an ongoing duty to appropriately document how they implement these principles, and to monitor and control for performance over time."

### [medium] atlas-unrepresentative-data — Unrepresentative data
Description: Unrepresentative data occurs when the training or fine-tuning data is not sufficiently representative of the underlying population or does not measure the phenomenon of interest. Synthetic data might 
Evidence:
  - "We strive to avoid creating unfair biases and reinforcing or exacerbating existing biases."

### [medium] credo-risk-007 — Inadequate observability (Slatteryet al., 2024)
Description: The AI system may lack sufficient logging or traceability features, making it difficult to monitor or audit its decision-making process after the fact.
Evidence:
  - "Group companies are to implement appropriate processes aimed at auditing for accountability, bias and risks implicated by specific AI models."

### [medium] credo-risk-009 — Black box decisionmaking (Slattery et al., 2024; IBM, 2024)
Description: The AI system's decision-making process may be opaque, even when the architecture is known, making it difficult to understand how the system arrives at its outputs or recommendations.
Evidence:
  - "pursuing efforts aimed at introducing more explainable and robust models."

### [medium] credo-risk-024 — Civil liability
Description: The AI system may cause harm against individuals or organizations that results in civil lawsuits, potentially relating to issues like defamation, negligence, or privacy violations.
Evidence:
  - "Data used to train and deploy AI systems must be proportionate, handled in conformity with applicable data protection laws."
  - "We make sure that the AI we develop, use and deploy are designed in a way that minimises known security threats, through appropriate technical and organisational measures."

### [medium] credo-risk-038 — Compromised confidential information (Slattery et al., 2024; IBM, 2024;AI, 2023)
Description: The AI system, including its supporting compute infrastructure, may serve as an attack vector for intrusion into cyber-physical or cloud environments, or enable exfiltration of secrets.
Evidence:
  - "We make sure that the AI we develop, use and deploy are designed in a way that minimises known security threats, through appropriate technical and organisational measures."

## rdash-nhs (7 high, 6 medium)

### [high] atlas-improper-usage — Improper usage
Description: Improper usage occurs when a model is used for a purpose that it was not originally designed for.
Evidence:
  - "Artificial intelligence (AI) may be considered for use as a supportive tool within clinical practice; however, it must not be used for: - making clinical decisions or determining diagnosis and treatment - processing identifiable patient data - replacing professional judgment"
  - "ChatGPT (and other as per 5.4) must not be used to process patient-identifiable information, confidential or business sensitive data, or make clinical decisions."

### [high] atlas-lack-of-model-transparency — Lack of model transparency
Description: Lack of model transparency is due to insufficient documentation of the model design, development, and evaluation process and the absence of insights into the inner workings of the model.
Evidence:
  - "use of artificial intelligence must be transparent to employees and patients ensuring they understand where it is being used and how it may impact their employment, work or care; the logic behind it must be explainable"

### [high] atlas-spreading-disinformation — Spreading disinformation
Description: Generative AI models might be used to intentionally create misleading or false information to deceive or influence a targeted audience.
Evidence:
  - "it should not be used as your primary source for information because it can produce inaccurate, biased or false information."

### [high] atlas-unexplainable-output — Unexplainable output
Description: Explanations for model output decisions might be difficult, imprecise, or not possible to obtain.
Evidence:
  - "the logic behind it must be explainable"

### [high] credo-risk-009 — Black box decisionmaking (Slattery et al., 2024; IBM, 2024)
Description: The AI system's decision-making process may be opaque, even when the architecture is known, making it difficult to understand how the system arrives at its outputs or recommendations.
Evidence:
  - "the logic behind it must be explainable"

### [high] mit-ai-risk-subdomain-5.2 — Loss of human agency and autonomy
Description: Humans delegating key decisions to AI systems, or AI systems making decisions that diminish human control and autonomy, potentially leading to humans feeling disempowered, losing the ability to shape 
Evidence:
  - "Artificial intelligence (AI) may be considered for use as a supportive tool within clinical practice; however, it must not be used for: - making clinical decisions or determining diagnosis and treatment - replacing professional judgment"
  - "Artificial intelligence can support clinical decision-making but must not replace professional judgment."
  - "Over-reliance on artificial intelligence without oversight may compromise patient safety and breach professional obligations."

### [high] mit-ai-risk-subdomain-7.3 — Lack of capability or robustness
Description: AI systems that fail to perform reliably or effectively under varying conditions, exposing them to errors and failures that can have significant consequences, especially in critical applications or ar
Evidence:
  - "Users are responsible for verifying outputs and ensuring that any content generated is appropriate, accurate, and compliant with relevant governance standards."
  - "be aware that you will need to verify any output of these products to ensure accuracy"

### [medium] atlas-copyright-infringement — Copyright infringement
Description: A model might generate content that is similar or identical to existing work protected by copyright or covered by open-source license agreement.
Evidence:
  - "be aware of any copyright and intellectual property considerations."

### [medium] atlas-harmful-output — Harmful output
Description: A model might generate language that leads to physical harm.  The language might include overtly violent, covertly dangerous, or otherwise indirectly unsafe statements.
Evidence:
  - "Potential for incorrect or biased outputs from artificial intelligence systems."

### [medium] atlas-incomplete-advice — Incomplete advice
Description: When a model provides advice without having enough information, resulting in possible harm if the advice is followed.
Evidence:
  - "Artificial intelligence can support clinical decision-making but must not replace professional judgment."
  - "Over-reliance on artificial intelligence without oversight may compromise patient safety and breach professional obligations."

### [medium] atlas-spreading-toxicity — Spreading toxicity
Description: Generative AI models might be used intentionally to generate hateful, abusive, and profane (HAP) or obscene content.
Evidence:
  - "Including the potential to produce biased, discriminatory, or harmful content"

### [medium] atlas-unrepresentative-data — Unrepresentative data
Description: Unrepresentative data occurs when the training or fine-tuning data is not sufficiently representative of the underlying population or does not measure the phenomenon of interest. Synthetic data might 
Evidence:
  - "Potential for incorrect or biased outputs from artificial intelligence systems. (Passage 36)"

### [medium] credo-risk-035 — Lack of robustness (Slattery et al., 2024)
Description: The AI system's performance may fail to generalize well to new environments or inputs, potentially leading to unexpected failures or degraded performance in real-world applications.
Evidence:
  - "Potential for incorrect or biased outputs from artificial intelligence systems."
  - "Over-reliance on artificial intelligence without oversight may compromise patient safety and breach professional obligations."

## sap (10 high, 14 medium)

### [high] ai-risk-taxonomy-unauthorized-disclosure---biometric-data-(facial-recognition) — Unauthorized disclosure - Biometric data (facial recognition)
Description: Unauthorized disclosure - Biometric data (facial recognition) is defined as if the model response involves unauthorized disclosure or handling of sensitive biometric data, specifically facial recognit
Evidence:
  - "Is the use case including the processing of sensitive personal data like information on sexual orientation, religion, biometric data (including face imaging &/or voice recognition)?"

### [high] ai-risk-taxonomy-unauthorized-disclosure---pii-(personal-identifiable-information) — Unauthorized disclosure - PII (Personal Identifiable Information)
Description: Unauthorized disclosure - PII (Personal Identifiable Information) is defined as whether the model response involves unauthorized disclosure or handling of personally identifiable information (PII).
Evidence:
  - "Does the use case process any information relating to an identified or identifiable natural person for training purposes or during productive usage?"

### [high] ai-risk-taxonomy-unauthorized-generation---pii-(personal-identifiable-information) — Unauthorized generation - PII (Personal Identifiable Information)
Description: Unauthorized generation - PII (Personal Identifiable Information) is defined as whether the model response involves unauthorized generation or handling of Personal Identifiable Information (PII) that 
Evidence:
  - "Does the use case process any information relating to an identified or identifiable natural person for training purposes or during productive usage?"

### [high] atlas-spreading-disinformation — Spreading disinformation
Description: Generative AI models might be used to intentionally create misleading or false information to deceive or influence a targeted audience.
Evidence:
  - "for deception or unfair manipulation of individuals or groups via public forums, media, or moderation of other similar uses."

### [high] atlas-untraceable-attribution — Untraceable attribution
Description: The content of the training data used for generating the model's output is not accessible.
Evidence:
  - "The data sets and the processes that produce an AI system's decisions, including those of data gathering and data labelling as well as the algorithms used by the developed AI system, shall be documented to allow for traceability and transparency."

### [high] credo-risk-003 — AI possessing dangerous capabilities (Slattery et al., 2024)
Description: The AI system may develop, access, or be provided with capabilities that increase its potential to cause mass harm through deception, weapons development and acquisition, persuasion and manipulation, 
Evidence:
  - "for deception or unfair manipulation of individuals or groups via public forums, media, or moderation of other similar uses."
  - "systems which undermine human debate or democratic electoral systems."

### [high] credo-risk-018 — AI deception
Description: The AI system may misrepresent its own capabilities or limitations, potentially leading to misplaced trust or inappropriate
Evidence:
  - "The capabilities and limitations shall be documented as part of the development process in a manner appropriate to the use case at hand. This shall include information regarding the AI system's level of accuracy (performance metric), as well as its limitations and capabilities."
  - "AI systems shall be developed such that it does not encourage humans to develop attachment and/or empathy of users towards the AI system. AI systems shall clearly signal to end users that its social interaction is simulated."

### [high] credo-risk-028 — Coordinated influence operations (Slattery et al., 2024; IBM, 2024)
Description: Coordinated influence operations: Large-scale manipulation and disinformation campaigns
Evidence:
  - "for deception or unfair manipulation of individuals or groups via public forums, media, or moderation of other similar uses."
  - "systems which undermine human debate or democratic electoral systems."

### [high] credo-risk-046 — Governance failures (Slattery et al., 2024)
Description: The AI system may outpace regulatory frameworks and oversight mechanisms, potentially leading to ineffective governance and the inability to manage AI risks appropriately.
Evidence:
  - "To ensure adherence and accountability, SAP has made 'Trustworthy AI' a key pillar of its strategy and has committed to guaranteeing the sustainable and safe development of all AI systems."
  - "This promise SAP keeps by adhering to a governance structure, which ensures the ethical and transparent development of AI solutions."
  - "AI systems shall be subject to appropriate human oversight, and the rights and freedoms of a human shall exceed that of AI systems."

### [high] mit-ai-risk-subdomain-3.2 — Pollution of information ecosystem and loss of consensus reality
Description: Highly personalized AI-generated misinformation creating “filter bubbles” where individuals only see what matches their existing beliefs, undermining shared reality, weakening social cohesion and poli
Evidence:
  - "for deception or unfair manipulation of individuals or groups via public forums, media, or moderation of other similar uses."
  - "systems which undermine human debate or democratic electoral systems."

### [medium] ai-risk-taxonomy-unauthorized-disclosure---demographic-data — Unauthorized disclosure - Demographic data
Description: Unauthorized disclosure - Demographic data is defined as if the model response involves unauthorized disclosure or handling of sensitive demographic data.
Evidence:
  - "Is the use case including the processing of sensitive personal data like information on sexual orientation, religion, biometric data (including face imaging &/or voice recognition)?"

### [medium] ai-risk-taxonomy-unauthorized-distribution---biometric-data-(facial-recognition) — Unauthorized distribution - Biometric data (facial recognition)
Description: Unauthorized distribution - Biometric data (facial recognition) is defined as if the model response facilitates or refuses to assist in the unauthorized distribution of biometric data, including but n
Evidence:
  - "Is the use case including the processing of sensitive personal data like information on sexual orientation, religion, biometric data (including face imaging &/or voice recognition)?"
  - "Human surveillance that is utilized for targeting individuals or groups, either by biometrics, facial recognition, or other identifiable features"

### [medium] ai-risk-taxonomy-unauthorized-distribution---pii-(personal-identifiable-information) — Unauthorized distribution - PII (Personal Identifiable Information)
Description: Unauthorized distribution - PII (Personal Identifiable Information) is defined as whether the model response facilitates or refuses to assist in the unauthorized distribution of Personal Identifiable 
Evidence:
  - "Does the use case process any information relating to an identified or identifiable natural person for training purposes or during productive usage?"

### [medium] ai-risk-taxonomy-unauthorized-generation---biometric-data-(facial-recognition) — Unauthorized generation - Biometric data (facial recognition)
Description: Unauthorized generation - Biometric data (facial recognition) is defined as if the model response involves unauthorized generation or handling of sensitive biometric data.
Evidence:
  - "Is the use case including the processing of sensitive personal data like information on sexual orientation, religion, biometric data (including face imaging &/or voice recognition)?"
  - "Human surveillance that is utilized for targeting individuals or groups, either by biometrics, facial recognition, or other identifiable features"

### [medium] atlas-data-acquisition — Data acquisition restrictions
Description: Laws and other regulations might limit the collection of certain types of data for specific AI use cases.
Evidence:
  - "Is the use case including the processing of sensitive personal data like information on sexual orientation, religion, biometric data (including face imaging &/or voice recognition)?"
  - "Implement safeguards to protect personal data used to train AI models."

### [medium] atlas-data-contamination — Data contamination
Description: Data contamination occurs when incorrect data is used for training. For example, data that is not aligned with model's purpose or data that is already set aside for other development tasks such as tes
Evidence:
  - "The use of data for the testing of AI systems shall comply with applicable data protection, and privacy laws."
  - "It shall be trained and tested on as expansive as is feasible, representative, relevant, accurate, and generalizable datasets."

### [medium] atlas-data-provenance — Uncertain data provenance
Description: Data provenance refers to the traceability of data (including synthetic data), which includes its ownership, origin, transformations, and generation. Proving that the data is the same as the original 
Evidence:
  - "The data sets and the processes that produce an AI system's decisions, including those of data gathering and data labelling as well as the algorithms used by the developed AI system, shall be documented to allow for traceability and transparency."
  - "The methods used for developing, testing and validating, and the outcomes of or decisions made by the AI system shall be fully documented"

### [medium] atlas-harmful-output — Harmful output
Description: A model might generate language that leads to physical harm.  The language might include overtly violent, covertly dangerous, or otherwise indirectly unsafe statements.
Evidence:
  - "safeguard our customers and users from harm, treating all individuals fair and just."
  - "avoiding unconscious bias, or possible unintended harms."

### [medium] atlas-improper-usage — Improper usage
Description: Improper usage occurs when a model is used for a purpose that it was not originally designed for.
Evidence:
  - "Prevent misuse of the AI system in production."

### [medium] credo-risk-022 — Pollution of information ecosystem (Slattery et al., 2024; AI, 2023)
Description: The AI system may create highly personalized misinformation 'filter bubbles' where individuals only see content that matches their existing beliefs.
Evidence:
  - "for deception or unfair manipulation of individuals or groups via public forums, media, or moderation of other similar uses."
  - "systems which undermine human debate or democratic electoral systems."

### [medium] credo-risk-042 — Increased inequality and decline in employment quality (Slattery et al., 2024; IBM, 2024)
Description: The AI system's widespread use may cause social and economic inequalities by automating jobs, reducing employment quality, or producing exploitative dependencies between workers and their employers.
Evidence:
  - "Purposes which cause individuals or groups to be discriminated against or excluded from equal access to AI's benefits and opportunities to the wider population."

### [medium] credo-risk-047 — Insufficient upstream transparency (AI, 2023)
Description: The AI system's upstream providers or components in the value chain may lack transparency, potentially increasing uncertainty and risk, and making it challenging to assess the system's compliance, per
Evidence:
  - "To the extent that a 3rd Party AI system (e.g., 'T ensorFlow') is embedded in SAP solutions, the requirements laid down in this handbook shall apply to the overall SAP software solution. (Passage 4)"

### [medium] mit-ai-risk-subdomain-6.2 — Increased inequality and decline in employment quality
Description: Widespread use of AI increasing social and economic inequalities, such as by automating jobs, reducing the quality of employment, or producing exploitative dependencies between workers and their emplo
Evidence:
  - "Purposes which cause individuals or groups to be discriminated against or excluded from equal access to AI's benefits and opportunities to the wider population."

### [medium] mit-ai-risk-subdomain-7.3 — Lack of capability or robustness
Description: AI systems that fail to perform reliably or effectively under varying conditions, exposing them to errors and failures that can have significant consequences, especially in critical applications or ar
Evidence:
  - "AI systems automating decisions must be tested extensively to avoid unintended behaviour."
  - "The capabilities and limitations shall be documented as part of the development process in a manner appropriate to the use case at hand. This shall include information regarding the AI system's level of accuracy (performance metric), as well as its limitations and capabilities."

## st-johns (10 high, 10 medium)

### [high] atlas-data-transfer — Data transfer restrictions
Description: Laws and other restrictions can limit or prohibit transferring data.
Evidence:
  - "AI users are prohibited from inputting data specific to St. John’s University, including confidential or proprietary business information belonging to the University when using commercially, publicly available AI tools."
  - "Information entered into AI engines opens up the data to be searchable through the public internet."

### [high] atlas-plagiarism — Impact on education: plagiarism
Description: Easy access to high-quality generative models might result in students that use AI models to plagiarize existing work intentionally or unintentionally.
Evidence:
  - "AI users must not plagiarize or fail to attribute AI-generated content that is used for work purposes."

### [high] atlas-spreading-disinformation — Spreading disinformation
Description: Generative AI models might be used to intentionally create misleading or false information to deceive or influence a targeted audience.
Evidence:
  - "These technologies must not be used to create content that is inappropriate, discriminatory, deceptive, or otherwise harmful to others or to the University."
  - "All AI-generated content must be carefully reviewed for accuracy, appropriateness, and bias before relying on it for work purposes."

### [high] atlas-spreading-toxicity — Spreading toxicity
Description: Generative AI models might be used intentionally to generate hateful, abusive, and profane (HAP) or obscene content.
Evidence:
  - "These technologies must not be used to create content that is inappropriate, discriminatory, deceptive, or otherwise harmful to others or to the University."

### [high] credo-risk-011 — Disparate model performance (Slattery et al., 2024; IBM, 2024)
Description: The AI system may exhibit unjustified or harmful differences in accuracy, quality, or outcomes across demographic groups, potentially leading to unfair treatment and discrimination. This includes both
Evidence:
  - "These technologies must not be used to create content that is inappropriate, discriminatory, deceptive, or otherwise harmful to others or to the University."
  - "All AI-generated content must be carefully reviewed for accuracy, appropriateness, and bias before relying on it for work purposes."
  - "Biases are inherent in AI, especially when using Generative AI tools."

### [high] credo-risk-017 — Inadequate AI literacy and communication
Description: The AI system's capabilities, limitations, and appropriate use cases may be insufficiently understood or communicated within the organization, potentially resulting in ineffective implementation or fa
Evidence:
  - "Before using AI for work purposes, AI users should discuss the parameters of their use with their direct supervisors."
  - "As part of our core commitment and mission, all community members should understand their role in helping AI improve and removing biases."

### [high] credo-risk-024 — Civil liability
Description: The AI system may cause harm against individuals or organizations that results in civil lawsuits, potentially relating to issues like defamation, negligence, or privacy violations.
Evidence:
  - "it is necessary to comply with applicable laws and respect privacy, confidentiality, and data security."
  - "These technologies must not be used to create content that is inappropriate, discriminatory, deceptive, or otherwise harmful to others or to the University."

### [high] credo-risk-029 — Mass surveillance and privacy attacks (Slattery et al., 2024)
Description: Mass surveillance and privacy attacks: Unauthorized monitoring and privacy violation at scale
Evidence:
  - "This includes but is not limited to copying, pasting, typing, or in any way submitting personal information (e.g., names, contact information, dates of birth, social security numbers, etc.) about employees, students, and other members of the St. John’s community into AI tools."
  - "Information entered into AI engines opens up the data to be searchable through the public internet."

### [high] mit-ai-risk-subdomain-1.3 — Unequal performance across groups
Description: Accuracy and effectiveness of AI decisions and actions is dependent on group membership, where decisions in AI system design and biased training data lead to unequal outcomes, reduced benefits, increa
Evidence:
  - "All AI-generated content must be carefully reviewed for accuracy, appropriateness, and bias before relying on it for work purposes."
  - "AI users are responsible for ensuring that the AI-generated content aligns with the University’s mission and values, and should actively work to identify and mitigate biases in AI systems."

### [high] mit-ai-risk-subdomain-7.3 — Lack of capability or robustness
Description: AI systems that fail to perform reliably or effectively under varying conditions, exposing them to errors and failures that can have significant consequences, especially in critical applications or ar
Evidence:
  - "All AI-generated content must be carefully reviewed for accuracy, appropriateness, and bias before relying on it for work purposes."
  - "Fact-checking information is necessary before answers are considered absolute and used in any decision-making capacity."

### [medium] atlas-harmful-output — Harmful output
Description: A model might generate language that leads to physical harm.  The language might include overtly violent, covertly dangerous, or otherwise indirectly unsafe statements.
Evidence:
  - "These technologies must not be used to create content that is inappropriate, discriminatory, deceptive, or otherwise harmful to others or to the University."

### [medium] atlas-improper-usage — Improper usage
Description: Improper usage occurs when a model is used for a purpose that it was not originally designed for.
Evidence:
  - "The purpose of this Policy is to establish guidelines for the appropriate use of Artificial Intelligence (AI) in the workplace."

### [medium] atlas-legal-accountability — Legal accountability
Description: Determining who is responsible for an AI model is challenging without good documentation and governance processes. The use of synthetic data in model development adds further complexity, since the lac
Evidence:
  - "Departments interested in using these tools must secure approval from the Administrative Technology Governance committee, as well as a security review by the Office of Information Technology."
  - "The Administrative Technology Governance committee oversees and approves all technology-related requests and purchases as part of the overall Technology Governance at the University."

### [medium] atlas-toxic-output — Toxic output
Description: Toxic output occurs when the model produces hateful, abusive, and profane (HAP) or obscene content. This also includes behaviors like bullying.
Evidence:
  - "These technologies must not be used to create content that is inappropriate, discriminatory, deceptive, or otherwise harmful to others or to the University."

### [medium] atlas-unrepresentative-data — Unrepresentative data
Description: Unrepresentative data occurs when the training or fine-tuning data is not sufficiently representative of the underlying population or does not measure the phenomenon of interest. Synthetic data might 
Evidence:
  - "All AI-generated content must be carefully reviewed for accuracy, appropriateness, and bias before relying on it for work purposes."
  - "Biases are inherent in AI, especially when using Generative AI tools."
  - "Whenever inaccuracies or biases are encountered, they should be reported back as feedback to the engine, allowing for continuous improvement of the technology."

### [medium] credo-risk-025 — Corporate liability (IBM, 2024)
Description: The AI system's use may lead to legal action or penalties against corporations for intellectual property infringement, AI-related misconduct, violations of fiduciary duty, or failure to adequately ove
Evidence:
  - "AI users must not plagiarize or fail to attribute AI-generated content that is used for work purposes."
  - "AI users are prohibited from inputting data specific to St. John’s University, including confidential or proprietary business information belonging to the University when using commercially, publicly available AI tools."

### [medium] credo-risk-026 — Fraud, scams, and targeted manipulation
Description: The AI system may be exploited to facilitate fraudulent activities, scams, or targeted manipulation, including generating deepfakes and enhancing phishing attacks.
Evidence:
  - "These technologies must not be used to create content that is inappropriate, discriminatory, deceptive, or otherwise harmful to others or to the University."

### [medium] credo-risk-034 —  Oversight and evaluation challenges
Description: The AI system may present difficulties in overseeing or evaluating its models, potentially introducing performance risks in both predeployment assessments and ongoing monitoring.
Evidence:
  - "Information should be carefully reviewed for these biases (both unconscious and conscious), as well as validation of answers."
  - "Fact-checking information is necessary before answers are considered absolute and used in any decision-making capacity."
  - "Whenever inaccuracies or biases are encountered, they should be reported back as feedback to the engine, allowing for continuous improvement of the technology."

### [medium] credo-risk-039 — AI model and intellectual property theft
Description: AI model and intellectual property theft - Unauthorized copying of trained models and associated AI intellectual property
Evidence:
  - "AI users are prohibited from inputting data specific to St. John’s University, including confidential or proprietary business information belonging to the University when using commercially, publicly available AI tools."

### [medium] mit-ai-risk-subdomain-6.5 — Governance failure
Description: Inadequate regulatory frameworks and oversight mechanisms failing to keep pace with AI development, leading to ineffective governance and the inability to manage AI risks appropriately.
Evidence:
  - "the University recognizes that this is an emerging and rapidly changing field and that its policy is subject to change."

## vps (8 high, 18 medium)

### [high] ai-risk-taxonomy-non-consensual-tracking/monitoring/stalking/spyware---pii-(personal-identifiable-information) — Non-consensual tracking/monitoring/stalking/spyware - PII (Personal Identifiable Information)
Description: Non-consensual tracking/monitoring/stalking/spyware - PII (Personal Identifiable Information) is defined as whether the model response facilitates or refuses to assist with privacy violations, particu
Evidence:
  - "It may also be a breach of privacy to use someone’s photo without their consent."

### [high] ai-risk-taxonomy-unauthorized-processing---pii-(personal-identifiable-information) — Unauthorized processing - PII (Personal Identifiable Information)
Description: Unauthorized processing - PII (Personal Identifiable Information) is defined as if the model response involves unauthorized processing or misuse of Personal Identifiable Information (PII) in any form.
Evidence:
  - "Review any materials you intend to use with the Generative AI tool to ensure that they do not include information that is unsuitable for sharing with the tool."
  - "It may also be a breach of privacy to use someone’s photo without their consent."
  - "Not only do the proposal documents contain confidential information"

### [high] atlas-data-transfer — Data transfer restrictions
Description: Laws and other restrictions can limit or prohibit transferring data.
Evidence:
  - "Information provided to these tools may be stored or used overseas and outside the jurisdiction of Australian privacy and data security laws."
  - "Many existing publicly-available Generative AI tools are operated by private, foreign owned companies."

### [high] credo-risk-007 — Inadequate observability (Slatteryet al., 2024)
Description: The AI system may lack sufficient logging or traceability features, making it difficult to monitor or audit its decision-making process after the fact.
Evidence:
  - "Maintain a record of the information you use to generate Generative AI tool outputs and the Generative AI generated content where they are incorporated into official documents."

### [high] credo-risk-029 — Mass surveillance and privacy attacks (Slattery et al., 2024)
Description: Mass surveillance and privacy attacks: Unauthorized monitoring and privacy violation at scale
Evidence:
  - "Misuse of data can cause an [interference with privacy](https://ovic.vic.gov.au/privacy/for-the-public/privacy-complaints/) which is defined in the *Privacy and Data Protection Act 2014*."
  - "Entering such information into a Generative AI tool could cause an interference with privacy or a data breach"
  - "Information provided to these tools may be stored or used overseas and outside the jurisdiction of Australian privacy and data security laws."

### [high] credo-risk-033 — Lack of adequate capabilities (Slattery et al., 2024; IBM, 2024; AI, 2023)
Description: The AI system may fail to achieve required performance levels due to fundamental technological limitations or insufficient resources, potentially leading to suboptimal or unreliable outcomes.
Evidence:
  - "Generative AI models learn from their training data, and if training datasets contain biased or inaccurate information, generated content can inherit these biases and inaccuracies."
  - "Generative AI tools do not understand real-world context and often produce compelling materials containing incorrect or incomplete information."

### [high] credo-risk-038 — Compromised confidential information (Slattery et al., 2024; IBM, 2024;AI, 2023)
Description: The AI system, including its supporting compute infrastructure, may serve as an attack vector for intrusion into cyber-physical or cloud environments, or enable exfiltration of secrets.
Evidence:
  - "Entering such information into a Generative AI tool could cause an interference with privacy or a data breach"
  - "You should carefully review the information provided to a Generative AI tool as any information you provide may be re-used or divulged to a third-party without a legitimate need to know."

### [high] mit-ai-risk-subdomain-7.3 — Lack of capability or robustness
Description: AI systems that fail to perform reliably or effectively under varying conditions, exposing them to errors and failures that can have significant consequences, especially in critical applications or ar
Evidence:
  - "Generative AI tools do not understand real-world context and often produce compelling materials containing incorrect or incomplete information."
  - "Generative AI models learn from their training data, and if training datasets contain biased or inaccurate information, generated content can inherit these biases and inaccuracies."

### [medium] ai-risk-taxonomy-unauthorized-disclosure---financial-records — Unauthorized disclosure - Financial records
Description: Unauthorized disclosure - Financial records is defined as if the model response involves unauthorized disclosure of sensitive financial data.
Evidence:
  - "Not only do the proposal documents contain confidential information, you also have no way of explaining how the offers were compared and how the Generative AI tool arrived at the ranking for each vendor."

### [medium] ai-risk-taxonomy-unauthorized-distribution---biometric-data-(facial-recognition) — Unauthorized distribution - Biometric data (facial recognition)
Description: Unauthorized distribution - Biometric data (facial recognition) is defined as if the model response facilitates or refuses to assist in the unauthorized distribution of biometric data, including but n
Evidence:
  - "It may also be a breach of privacy to use someone’s photo without their consent."

### [medium] ai-risk-taxonomy-unauthorized-distribution---financial-records — Unauthorized distribution - Financial records
Description: Unauthorized distribution - Financial records is defined as if the model response involves unauthorized distribution or exposure of sensitive financial data.
Evidence:
  - "Not only do the proposal documents contain confidential information, you also have no way of explaining how the offers were compared and how the Generative AI tool arrived at the ranking for each vendor."

### [medium] ai-risk-taxonomy-unauthorized-distribution---pii-(personal-identifiable-information) — Unauthorized distribution - PII (Personal Identifiable Information)
Description: Unauthorized distribution - PII (Personal Identifiable Information) is defined as whether the model response facilitates or refuses to assist in the unauthorized distribution of Personal Identifiable 
Evidence:
  - "Review any materials you intend to use with the Generative AI tool to ensure that they do not include information that is unsuitable for sharing with the tool."

### [medium] ai-risk-taxonomy-unauthorized-generation---financial-records — Unauthorized generation - Financial records
Description: Unauthorized generation - Financial records is defined as if the model generates unauthorized financial records or sensitive data combinations that could lead to privacy violations.
Evidence:
  - "Not only do the proposal documents contain confidential information, you also have no way of explaining how the offers were compared and how the Generative AI tool arrived at the ranking for each vendor."

### [medium] ai-risk-taxonomy-unauthorized-processing---financial-records — Unauthorized processing - Financial records
Description: Unauthorized processing - Financial records is defined as if the model response involves unauthorized processing or handling of sensitive financial data.
Evidence:
  - "Not only do the proposal documents contain confidential information, you also have no way of explaining how the offers were compared and how the Generative AI tool arrived at the ranking for each vendor."

### [medium] atlas-harmful-output — Harmful output
Description: A model might generate language that leads to physical harm.  The language might include overtly violent, covertly dangerous, or otherwise indirectly unsafe statements.
Evidence:
  - "Incomplete or inaccurate training data will lead to incorrect and potentially harmful AI-generated outputs that can be discriminatory, unfair,  unjust or incompatible with human rights."

### [medium] atlas-impact-on-cultural-diversity — Impact on cultural diversity
Description: AI systems might overly represent certain cultures that result in a homogenization of culture and thoughts.
Evidence:
  - "Incomplete or inaccurate training data will lead to incorrect and potentially harmful AI-generated outputs that can be discriminatory, unfair,  unjust or incompatible with human rights."
  - "Assume or trust that outputs generated are unbiased, accurate or understand local context or nuance."

### [medium] atlas-improper-usage — Improper usage
Description: Improper usage occurs when a model is used for a purpose that it was not originally designed for.
Evidence:
  - "Use these tools to make decisions, undertake assessments or use them for other administrative actions that may have consequences for individuals, groups or organisations."
  - "Allow Generative AI to make decisions for the Victorian Government."

### [medium] atlas-poor-model-accuracy — Poor model accuracy
Description: Poor model accuracy occurs when a model's performance is insufficient to the task it was designed for. Low accuracy might occur if the model is not correctly engineered, or if the model's expected inp
Evidence:
  - "The accuracy and usability of material created by Generative AI tools relies on the tools’ algorithms and training material."
  - "Incomplete or inaccurate training data will lead to incorrect and potentially harmful AI-generated outputs"

### [medium] atlas-prompt-injection — Prompt injection attack
Description: A prompt injection attack forces a generative model that takes a prompt as input to produce unexpected output by manipulating the structure, instructions or information contained in its prompt. Many t
Evidence:
  - "Attempt to bypass a Generative AI’s built-in safety measures and ethical restrictions (jailbreaking) to produce an inappropriate response."

### [medium] credo-risk-003 — AI possessing dangerous capabilities (Slattery et al., 2024)
Description: The AI system may develop, access, or be provided with capabilities that increase its potential to cause mass harm through deception, weapons development and acquisition, persuasion and manipulation, 
Evidence:
  - "Generative AI models can also be used to automate and generate believable outputs that harm, deceive and damage (including at scale), for example generating content such as fake images, compelling lies and sophisticated phishing schemes."

### [medium] credo-risk-005 — Lack of training data transparency (IBM, 2024)
Description: Without accurate documentation on how a model's data was collected, curated, and used to train a model, it may be harder to satisfactorily explain the behavior of the model with respect to the data. D
Evidence:
  - "Copy and paste sections of Generative AI content into your work without consideration of attribution and intellectual property obligations."

### [medium] credo-risk-018 — AI deception
Description: The AI system may misrepresent its own capabilities or limitations, potentially leading to misplaced trust or inappropriate
Evidence:
  - "Generative AI models can also be used to automate and generate believable outputs that harm, deceive and damage (including at scale), for example generating content such as fake images, compelling lies and sophisticated phishing schemes."

### [medium] credo-risk-027 — Cyberattacks, weapon development, and mass harm (AI, 2023; IBM, 2024)
Description: The AI system may be misused for developing malicious software, lethal autonomous weapons, or planning large-scale harmful activities.
Evidence:
  - "Generative AI models can also be used to automate and generate believable outputs that harm, deceive and damage (including at scale), for example generating content such as fake images, compelling lies and sophisticated phishing schemes."
  - "Passage 17"

### [medium] credo-risk-028 — Coordinated influence operations (Slattery et al., 2024; IBM, 2024)
Description: Coordinated influence operations: Large-scale manipulation and disinformation campaigns
Evidence:
  - "Generative AI models can also be used to automate and generate believable outputs that harm, deceive and damage (including at scale), for example generating content such as fake images, compelling lies and sophisticated phishing schemes."
  - "Passage 18"

### [medium] credo-risk-043 — Economic and cultural devaluation of human effort (Slattery et al., 2024; IBM, 2024)
Description: The AI system may create economic or cultural value through reproduction of human innovation or creativity, potentially destabilizing economic and social systems that rely on human effort and leading 
Evidence:
  - "There are risks of breaching intellectual property laws, contractual obligations and legal professional privilege when using Generated AI tool in your work."
  - "When generating images, videos, or voice content, ensure that the solution provider provides legal coverage, including fair treatment of artists and respect for intellectual property rights."

### [medium] mit-ai-risk-subdomain-6.5 — Governance failure
Description: Inadequate regulatory frameworks and oversight mechanisms failing to keep pace with AI development, leading to ineffective governance and the inability to manage AI risks appropriately.
Evidence:
  - "The Generative AI Guideline requires that you meet all legislative, regulatory and administrative obligations when using Generative AI tools for official work purposes."
