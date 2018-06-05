** TODO List **


1. Refactor the Mantid reduction hierarchy for PyVDrive-Vulcan-Reduction 2.0
  a) goal 1: replace SNSPowderReduciton
  b) goal 2: unify the reduction workflow for single run reduction and chopped run reduction
  c) target code structure
    i.   API: bridge between UI and library
    ii.  Project manager: placeholder for ReductionManager
    iii. Reduction manager: placeholder of data file, raw workspace and reduced workspace, reduction states
    iv.  mantid_reduction: wrapper on Mantid reduction algorithms


Glossary:
1. Reduction: align and focus powder optionally with filtering bad pulses and etc