import boto3
import json

class PII:
    # Initialize the class setting the defaults.
    # This needs to pass in the textract json
    def __init__(self,
                 # Language for comprehend to use
                 language: str = 'en',
                 # The score you want to accept from comprehend
                 confidence_score: float = 0.01,
                 # The PII types you want to filter out if left blank it will flag all types
                 types: list = None
                 ):
        self.comprehend = boto3.client('comprehend')
        self.lang_str = language
        self.keyList = []
        self.offsetlist = []
        self.textract_response = None
        self.comprehend_response = None
        self.filtered_comprehend = None
        self.text_block = ""
        self.confidence = confidence_score
        self.type_filter = types

        # This takes the filtered comprehend response

    def __find_pii_from_filtered_comprehend(self):
        for detection in self.filtered_comprehend:
            for i in range(0, len(self.offsetlist) - 1):
                if detection.get('BeginOffset') <= self.offsetlist[i] <= detection.get('EndOffset'):
                    self.keyList[i].update(detection)

                    print(self.keyList[i])
        return self

    # This function accepts the comprehend response
    # Creates a filtered response based on score and type
    def __filter_pii(self):
        self.filtered_comprehend = []
        for entity in self.comprehend_response.get('Entities'):
            if (self.confidence <= entity.get('Score') and self.type_filter is None) \
                    or (self.confidence <= entity.get('Score') and entity.get('Type') in self.type_filter):
                self.filtered_comprehend.append(entity)
        return self.filtered_comprehend

    # Reconstruct the text into a multi line paragraph
    # Builds keyDict
    def __reconstruct_doc(self):
        total_length = 0
        for blocks in self.textract_response:
            for block in blocks.get('Blocks'):
                if block.get('BlockType') == 'WORD':
                    word = block.get('Text')
                    self.offsetlist.append(total_length)
                    self.text_block = f"{self.text_block}{word} "
                    self.keyList.append({
                        'Word': word,
                        'Geometry': block.get('Geometry')
                    })
                    total_length += len(word) + 1
            return self

    # This function accepts the json from textract and passes it to __reconstruct_doc to
    # generate a multi line string then passes that to comprehend and returns the response
    def __get_comprehend(self):
        if len(self.text_block) == 0:
            self.__reconstruct_doc()
        self.comprehend_response = self.comprehend.detect_pii_entities(
            Text=self.text_block,
            LanguageCode=self.lang_str
        )

        return self

    def ExecuteTextract2Comprehend(self, textract_response):
        self.textract_response = textract_response
        self.__get_comprehend()
        self.__filter_pii()
        self.__find_pii_from_filtered_comprehend()

        return self


if __name__ == '__main__':
    data = open('../tests/pii_test/pii_image_example-png-response.json', 'r')
    textract_response = json.load(data)
    textract2comprehend = PII(language='en')
    pii_response = textract2comprehend.ExecuteTextract2Comprehend(textract_response)

    print(pii_response)
