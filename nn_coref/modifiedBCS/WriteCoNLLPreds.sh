#!/bin/sh
exec scala -J-Xmx3G -classpath "moarcoref-assembly-1.jar:lib/futile.jar:lib/BerkeleyParser-1.7.jar" "$0" "$@"
!#

import java.io._
import scala.collection.mutable.ListBuffer
import scala.collection.mutable.ArrayBuffer
import scala.collection.mutable.HashMap
import scala.io.Source
import edu.berkeley.nlp.coref.NumberGenderComputer
import edu.berkeley.nlp.coref._
import edu.berkeley.nlp.futile.fig.basic.IOUtils
import edu.berkeley.nlp.futile.util.Logger

object BP2CoNLL {

  // the following two functions are just copied from BCS CorefSystem.scala
  def checkFileReachableForRead(file: String, msg: String) {
    if (file.isEmpty) {
      throw new RuntimeException("Undefined " + msg + "; must be defined for the mode you're running in");
    }
    if (!new File(file).exists()) {
      throw new RuntimeException(msg + " file/directory doesn't exist for read: " + file);
    }
  }
  def checkFileReachableForWrite(file: String, msg: String) {
    if (file.isEmpty) {
      throw new RuntimeException("Undefined " + msg + "; must be defined for the mode you're running in");
    }
    
    if (file.contains("/") && !new File(file).getParentFile().exists()) {
      throw new RuntimeException(msg + " file/directory couldn't be opened for write: " + file);
    }
  }

  // same as original, except we sort files by names so we can dump features and then repredict  
  def loadRawConllDocs(path: String, size: Int, gold: Boolean): Seq[ConllDoc] = {
    val suffix = if (gold) "gold_conll" else Driver.docSuffix;
    Logger.logss("Loading " + size + " docs from " + path + " ending with " + suffix);
    val files = new File(path).listFiles().filter(file => file.getAbsolutePath.endsWith(suffix)); //.sorted;
    val reader = new ConllDocReader(Driver.lang);
    val docs = new ArrayBuffer[ConllDoc];
    var docCounter = 0;
    var fileIdx = 0;
    while (fileIdx < files.size && (size == -1 || docCounter < size)) {
      val newDocs = reader.readConllDocs(files(fileIdx).getAbsolutePath);
      docs ++= newDocs;
      docCounter += newDocs.size
      fileIdx += 1;
    }
    val numDocs = if (size == -1) docs.size else Math.min(size, files.size);
    Logger.logss(docs.size + " docs loaded from " + fileIdx + " files, retaining " + numDocs);
    if (docs.size == 0) {
      Logger.logss("WARNING: Zero docs loaded...double check your paths unless you meant for this happen");
    }
    val docsToUse = docs.slice(0, numDocs);
    docsToUse;
  }
  
  // same as in original
  def loadCorefDocs(path: String, size: Int, numberGenderComputer: NumberGenderComputer, gold: Boolean): Seq[CorefDoc] = {
    val docs = loadRawConllDocs(path, size, gold);
    val assembler = CorefDocAssembler(Driver.lang, Driver.useGoldMentions);
    val mentionPropertyComputer = new MentionPropertyComputer(numberGenderComputer);
    val corefDocs = docs.map(doc => assembler.createCorefDoc(doc, mentionPropertyComputer));
    CorefDoc.checkGoldMentionRecall(corefDocs);
    corefDocs;
  }
  
  def computeMentionIndices(doc: DocumentGraph) : Seq[Tuple2[Int, Int]] = {
    val indexMap = new HashMap[Tuple2[Int, Int], Int]
    var docIndex = 0;
    for (sent <- 0 until doc.corefDoc.rawDoc.words.size) {
      val sentWords = doc.corefDoc.rawDoc.words(sent)
      for (word <- 0 until sentWords.size) {
        indexMap((sent, word)) = docIndex;
        docIndex += 1;
      }
      // end of sentence = beginning of the next sentence
      indexMap((sent, sentWords.size)) = docIndex; 
    }
    val mentionIndices = new ArrayBuffer[Tuple2[Int, Int]];
    for (m <- doc.getMentions()) {
      val newElem = (indexMap((m.sentIdx, m.startIdx)),
                     indexMap((m.sentIdx, m.endIdx)));
      mentionIndices += newElem;
    }
    return mentionIndices;
  }
 
  def main(args: Array[String]) {
    val indir = args(0);
    val bpfi = args(1);
    val outdir = args(2);
    val devPath = args(3);    
    val ngPath = args(4);
    val numberGenderComputer = NumberGenderComputer.readBergsmaLinData(ngPath);
    // (Minh 21 Apr 2017) tried to remove sorting to maintain original 
    // document order but ran into error at postprocessForConll() call.
    val devDGs = loadCorefDocs(devPath, -1, numberGenderComputer, false).map(new DocumentGraph(_, false)).sortBy(_.corefDoc.rawDoc.printableDocName);    
    //val files = new File(indir).listFiles().filter(file => file.getAbsolutePath.contains(".bps"));
    val files = new File(indir).listFiles().filter(file => file.getAbsolutePath.contains(bpfi));
    for (fi <- files) {
      println("doing " + fi.getAbsolutePath());
      val bps = ListBuffer[Array[Int]]();
      for (line <- Source.fromFile(fi.getAbsolutePath()).getLines()) {
        val preds = line.split(' ');
        bps += preds.map(x => x.toInt);
      }
      val allPredBackptrs = bps.toArray;
      val allPredClusterings = (0 until devDGs.size).map(i => OrderedClustering.createFromBackpointers(allPredBackptrs(i))).toArray;
      val writer = IOUtils.openOutHard(outdir+"/" + fi.getName() + ".out");
      val writer2 = IOUtils.openOutHard(outdir+"/" + fi.getName() + ".antecedents");
      for (i <- 0 until devDGs.size) {
        val mentionIndices = computeMentionIndices(devDGs(i));
        for (j <- 0 until allPredBackptrs(i).size) {
          if  (allPredBackptrs(i)(j) != j) {
            val doc = devDGs(i).corefDoc.rawDoc;
            val docName = f"(${doc.docID}%s); part ${doc.docPartNo}%03d"
            val men = mentionIndices(j)
            val ante = mentionIndices(allPredBackptrs(i)(j))
            writer2.println(s"$docName\t(${men._1}, ${men._2-1})\t(${ante._1}, ${ante._2-1})")
          }
        }
        val outputClustering = new OrderedClusteringBound(devDGs(i).getMentions, allPredClusterings(i));
        ConllDocWriter.writeDoc(writer, devDGs(i).corefDoc.rawDoc, outputClustering.postprocessForConll());
      }
      writer.close();
      writer2.close();
    } 
  }
 
}

BP2CoNLL.main(args)
