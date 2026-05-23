// Constraints (idempotent)
CREATE CONSTRAINT segment_name IF NOT EXISTS FOR (s:Segment) REQUIRE s.name IS UNIQUE;
CREATE CONSTRAINT comp_name IF NOT EXISTS FOR (c:Competitor) REQUIRE c.name IS UNIQUE;
CREATE CONSTRAINT regime_name IF NOT EXISTS FOR (r:Regulation) REQUIRE r.name IS UNIQUE;

// Wipe before re-seed
MATCH (n) DETACH DELETE n;

// Seed
CREATE (sr:Segment {name:"Small Retailers", size:"high", wtp:"low", friction:"low"});
CREATE (ec:Segment {name:"Enterprise Chains", size:"high", wtp:"high", friction:"high"});
CREATE (ts:Segment {name:"Tech-savvy Stores", size:"med", wtp:"med", friction:"med"});
CREATE (po:Segment {name:"Privacy Focused Orgs", size:"med", wtp:"med", friction:"high"});

CREATE (c1:Competitor {name:"AdTechCorp", strength:0.8});
CREATE (c2:Competitor {name:"RetailAI Inc", strength:0.6});
CREATE (c3:Competitor {name:"CCTV Cloud", strength:0.5});

CREATE (r1:Regulation {name:"Biometric Data Act", region:"EU", strictness:0.9});
CREATE (r2:Regulation {name:"State Privacy Law", region:"US-CA", strictness:0.7});

CREATE (c1)-[:COMPETES_IN]->(ec);
CREATE (c2)-[:COMPETES_IN]->(sr);
CREATE (c3)-[:COMPETES_IN]->(ts);
CREATE (r1)-[:CONSTRAINS]->(po);
CREATE (r2)-[:CONSTRAINS]->(ec);
CREATE (sr)-[:INFLUENCES {weight:0.4}]->(ts);
CREATE (ts)-[:INFLUENCES {weight:0.6}]->(ec);
