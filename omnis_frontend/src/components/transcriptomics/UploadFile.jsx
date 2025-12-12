"use client"

import { useState } from "react"
import { Upload, FileText, Download, AlertCircle, CheckCircle, Info, HelpCircle } from "lucide-react"
import Navbar from "../Navbar"

const UploadPage = () => {
  const [fastqFiles, setFastqFiles] = useState([])
  const [metadataFile, setMetadataFile] = useState(null)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadComplete, setUploadComplete] = useState(false)
  const [activeTab, setActiveTab] = useState("instructions")

  const handleFastqDrop = (e) => {
    e.preventDefault()
    const files = Array.from(e.dataTransfer.files).filter(
      (file) =>
        file.name.endsWith(".fastq") ||
        file.name.endsWith(".fq") ||
        file.name.endsWith(".fastq.gz") ||
        file.name.endsWith(".fq.gz"),
    )
    setFastqFiles((prev) => [...prev, ...files])
  }

  const handleFastqSelect = (e) => {
    const files = Array.from(e.target.files).filter(
      (file) =>
        file.name.endsWith(".fastq") ||
        file.name.endsWith(".fq") ||
        file.name.endsWith(".fastq.gz") ||
        file.name.endsWith(".fq.gz"),
    )
    setFastqFiles((prev) => [...prev, ...files])
  }

  const handleMetadataSelect = (e) => {
    if (e.target.files.length > 0) {
      setMetadataFile(e.target.files[0])
    }
  }

  const removeFastqFile = (index) => {
    setFastqFiles((prev) => prev.filter((_, i) => i !== index))
  }

  const removeMetadataFile = () => {
    setMetadataFile(null)
  }

  const downloadMetadataTemplate = () => {
    // In a real application, this would download an actual template file
    // For this example, we'll create a simple CSV template
    const template =
      "sample_id,condition,replicate,paired_end,read_length,sequencing_platform\nsample1,treatment,1,true,150,Illumina\nsample2,control,1,true,150,Illumina"
    const blob = new Blob([template], { type: "text/csv" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = "rna_seq_metadata_template.csv"
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const simulateUpload = () => {
    if (fastqFiles.length === 0) return

    setIsUploading(true)
    setUploadProgress(0)
    setUploadComplete(false)

    const interval = setInterval(() => {
      setUploadProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval)
          setIsUploading(false)
          setUploadComplete(true)
          return 100
        }
        return prev + 5
      })
    }, 300)
  }

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Navbar />

      <main className="flex-grow container mx-auto px-4 py-8">
        <div className="max-w-5xl mx-auto">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">RNA-Sequencing Data Upload</h1>
          <p className="text-gray-600 mb-8">Upload your FASTQ files and optional metadata for RNA-seq analysis</p>

          <div className="bg-white rounded-lg shadow-md overflow-hidden mb-8">
            <div className="flex border-b">
              <button
                className={`px-6 py-3 font-medium ${activeTab === "instructions" ? "text-purple-600 border-b-2 border-purple-600" : "text-gray-600 hover:text-purple-600"}`}
                onClick={() => setActiveTab("instructions")}
              >
                Instructions
              </button>
              <button
                className={`px-6 py-3 font-medium ${activeTab === "upload" ? "text-purple-600 border-b-2 border-purple-600" : "text-gray-600 hover:text-purple-600"}`}
                onClick={() => setActiveTab("upload")}
              >
                Upload Files
              </button>
            </div>

            <div className="p-6">
              {activeTab === "instructions" ? (
                <div className="space-y-6">
                  <div className="bg-purple-50 p-4 rounded-md border border-purple-100">
                    <div className="flex items-start">
                      <Info className="h-5 w-5 text-purple-600 mt-0.5 mr-3 flex-shrink-0" />
                      <p className="text-purple-800">
                        RNA-sequencing data analysis requires properly formatted FASTQ files and accurate metadata.
                        Please follow the guidelines below to ensure successful processing.
                      </p>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-xl font-semibold text-gray-800 mb-3">FASTQ File Requirements</h3>
                    <ul className="list-disc pl-5 space-y-2 text-gray-700">
                      <li>Files must be in FASTQ format (.fastq, .fq) or compressed (.fastq.gz, .fq.gz)</li>
                      <li>For paired-end reads, ensure both forward (R1) and reverse (R2) files are uploaded</li>
                      <li>
                        File naming convention should follow:{" "}
                        <code className="bg-gray-100 px-1 py-0.5 rounded">sample_id_R1.fastq.gz</code> and{" "}
                        <code className="bg-gray-100 px-1 py-0.5 rounded">sample_id_R2.fastq.gz</code>
                      </li>
                      <li>Maximum file size: 10GB per file</li>
                    </ul>
                  </div>

                  <div>
                    <h3 className="text-xl font-semibold text-gray-800 mb-3">Metadata Requirements</h3>
                    <p className="mb-3 text-gray-700">
                      A metadata file is optional but highly recommended for comprehensive analysis. The file should be
                      in CSV format with the following columns:
                    </p>
                    <div className="overflow-x-auto">
                      <table className="min-w-full border border-gray-200 rounded-md">
                        <thead className="bg-gray-100">
                          <tr>
                            <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">Column</th>
                            <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">Description</th>
                            <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">Required</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                          <tr>
                            <td className="px-4 py-2 text-sm text-gray-700">sample_id</td>
                            <td className="px-4 py-2 text-sm text-gray-700">Unique identifier for each sample</td>
                            <td className="px-4 py-2 text-sm text-gray-700">Yes</td>
                          </tr>
                          <tr>
                            <td className="px-4 py-2 text-sm text-gray-700">condition</td>
                            <td className="px-4 py-2 text-sm text-gray-700">
                              Experimental condition (e.g., treatment, control)
                            </td>
                            <td className="px-4 py-2 text-sm text-gray-700">Yes</td>
                          </tr>
                          <tr>
                            <td className="px-4 py-2 text-sm text-gray-700">replicate</td>
                            <td className="px-4 py-2 text-sm text-gray-700">
                              Biological or technical replicate number
                            </td>
                            <td className="px-4 py-2 text-sm text-gray-700">Yes</td>
                          </tr>
                          <tr>
                            <td className="px-4 py-2 text-sm text-gray-700">paired_end</td>
                            <td className="px-4 py-2 text-sm text-gray-700">
                              Whether the sample is paired-end (true/false)
                            </td>
                            <td className="px-4 py-2 text-sm text-gray-700">Yes</td>
                          </tr>
                          <tr>
                            <td className="px-4 py-2 text-sm text-gray-700">read_length</td>
                            <td className="px-4 py-2 text-sm text-gray-700">Length of sequencing reads</td>
                            <td className="px-4 py-2 text-sm text-gray-700">No</td>
                          </tr>
                          <tr>
                            <td className="px-4 py-2 text-sm text-gray-700">sequencing_platform</td>
                            <td className="px-4 py-2 text-sm text-gray-700">Platform used for sequencing</td>
                            <td className="px-4 py-2 text-sm text-gray-700">No</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                    <div className="mt-4">
                      <button
                        onClick={downloadMetadataTemplate}
                        className="flex items-center text-purple-600 hover:text-purple-700 font-medium"
                      >
                        <Download className="h-4 w-4 mr-2" />
                        Download Metadata Template
                      </button>
                    </div>
                  </div>

                  <div className="flex justify-end">
                    <button
                      onClick={() => setActiveTab("upload")}
                      className="px-6 py-2 bg-purple-600 text-white rounded-md font-medium hover:bg-purple-700"
                    >
                      Proceed to Upload
                    </button>
                  </div>
                </div>
              ) : (
                <div className="space-y-8">
                  {/* FASTQ Files Upload */}
                  <div>
                    <h3 className="text-xl font-semibold text-gray-800 mb-4">Upload FASTQ Files</h3>
                    <div
                      className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-purple-400 transition-colors"
                      onDragOver={(e) => e.preventDefault()}
                      onDrop={handleFastqDrop}
                    >
                      <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-700 mb-2">Drag and drop your FASTQ files here</p>
                      <p className="text-gray-500 text-sm mb-4">or</p>
                      <label className="px-4 py-2 bg-purple-600 text-white rounded-md font-medium hover:bg-purple-700 cursor-pointer">
                        Browse Files
                        <input
                          type="file"
                          multiple
                          accept=".fastq,.fq,.fastq.gz,.fq.gz"
                          className="hidden"
                          onChange={handleFastqSelect}
                        />
                      </label>
                      <p className="text-gray-500 text-sm mt-4">Accepted formats: .fastq, .fq, .fastq.gz, .fq.gz</p>
                    </div>

                    {fastqFiles.length > 0 && (
                      <div className="mt-4">
                        <h4 className="font-medium text-gray-700 mb-2">Selected Files ({fastqFiles.length})</h4>
                        <div className="max-h-60 overflow-y-auto">
                          <ul className="space-y-2">
                            {fastqFiles.map((file, index) => (
                              <li key={index} className="flex items-center justify-between bg-gray-50 p-3 rounded-md">
                                <div className="flex items-center">
                                  <FileText className="h-5 w-5 text-purple-600 mr-2" />
                                  <div>
                                    <p className="text-sm font-medium text-gray-700">{file.name}</p>
                                    <p className="text-xs text-gray-500">{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
                                  </div>
                                </div>
                                <button
                                  onClick={() => removeFastqFile(index)}
                                  className="text-gray-500 hover:text-red-500"
                                >
                                  <svg
                                    xmlns="http://www.w3.org/2000/svg"
                                    className="h-5 w-5"
                                    viewBox="0 0 20 20"
                                    fill="currentColor"
                                  >
                                    <path
                                      fillRule="evenodd"
                                      d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                                      clipRule="evenodd"
                                    />
                                  </svg>
                                </button>
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Metadata File Upload */}
                  <div>
                    <h3 className="text-xl font-semibold text-gray-800 mb-4">Upload Metadata File (Optional)</h3>
                    <div className="flex items-center">
                      <div className="flex-grow">
                        <label className="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-md font-medium hover:bg-gray-50 cursor-pointer inline-flex items-center">
                          <Upload className="h-4 w-4 mr-2" />
                          Select Metadata File
                          <input
                            type="file"
                            accept=".csv,.tsv,.txt"
                            className="hidden"
                            onChange={handleMetadataSelect}
                          />
                        </label>
                        <span className="ml-3 text-sm text-gray-500">Accepted formats: .csv, .tsv, .txt</span>
                      </div>
                      <button
                        onClick={downloadMetadataTemplate}
                        className="flex items-center text-purple-600 hover:text-purple-700 font-medium"
                      >
                        <Download className="h-4 w-4 mr-2" />
                        Download Template
                      </button>
                    </div>

                    {metadataFile && (
                      <div className="mt-4">
                        <div className="flex items-center justify-between bg-gray-50 p-3 rounded-md">
                          <div className="flex items-center">
                            <FileText className="h-5 w-5 text-purple-600 mr-2" />
                            <div>
                              <p className="text-sm font-medium text-gray-700">{metadataFile.name}</p>
                              <p className="text-xs text-gray-500">{(metadataFile.size / 1024).toFixed(2)} KB</p>
                            </div>
                          </div>
                          <button onClick={removeMetadataFile} className="text-gray-500 hover:text-red-500">
                            <svg
                              xmlns="http://www.w3.org/2000/svg"
                              className="h-5 w-5"
                              viewBox="0 0 20 20"
                              fill="currentColor"
                            >
                              <path
                                fillRule="evenodd"
                                d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                                clipRule="evenodd"
                              />
                            </svg>
                          </button>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Upload Progress and Button */}
                  <div className="space-y-4">
                    {(isUploading || uploadComplete) && (
                      <div className="w-full bg-gray-200 rounded-full h-2.5">
                        <div
                          className="bg-purple-600 h-2.5 rounded-full transition-all duration-300"
                          style={{ width: `${uploadProgress}%` }}
                        ></div>
                      </div>
                    )}

                    {uploadComplete && (
                      <div className="flex items-start p-4 bg-green-50 text-green-800 rounded-md">
                        <CheckCircle className="h-5 w-5 text-green-500 mt-0.5 mr-3 flex-shrink-0" />
                        <div>
                          <p className="font-medium">Upload Complete!</p>
                          <p className="text-sm">
                            Your files have been successfully uploaded. You will receive a notification when processing
                            is complete.
                          </p>
                        </div>
                      </div>
                    )}

                    {fastqFiles.length === 0 && (
                      <div className="flex items-start p-4 bg-amber-50 text-amber-800 rounded-md">
                        <AlertCircle className="h-5 w-5 text-amber-500 mt-0.5 mr-3 flex-shrink-0" />
                        <p>Please select at least one FASTQ file to upload.</p>
                      </div>
                    )}

                    <div className="flex justify-between items-center">
                      <button
                        onClick={() => setActiveTab("instructions")}
                        className="px-6 py-2 border border-gray-300 text-gray-700 rounded-md font-medium hover:bg-gray-50"
                      >
                        Back to Instructions
                      </button>

                      <button
                        onClick={simulateUpload}
                        disabled={fastqFiles.length === 0 || isUploading}
                        className={`px-6 py-2 bg-purple-600 text-white rounded-md font-medium ${
                          fastqFiles.length === 0 || isUploading
                            ? "opacity-50 cursor-not-allowed"
                            : "hover:bg-purple-700"
                        }`}
                      >
                        {isUploading ? "Uploading..." : "Start Upload"}
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Help Section */}
          <div className="bg-white rounded-lg shadow-md overflow-hidden">
            <div className="p-6">
              <div className="flex items-start">
                <HelpCircle className="h-6 w-6 text-purple-600 mt-0.5 mr-3 flex-shrink-0" />
                <div>
                  <h3 className="text-lg font-semibold text-gray-800 mb-2">Need Help?</h3>
                  <p className="text-gray-600 mb-4">
                    If you're experiencing issues with file uploads or have questions about the required format, our
                    support team is here to help.
                  </p>
                  <div className="flex flex-wrap gap-4">
                    <a href="#" className="text-purple-600 hover:text-purple-700 font-medium">
                      View Documentation
                    </a>
                    <a href="#" className="text-purple-600 hover:text-purple-700 font-medium">
                      Contact Support
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default UploadPage
